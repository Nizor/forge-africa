import hashlib
import hmac
import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone
import requests

from apps.accounts.decorators import ClientRequiredMixin
from apps.orders.models import Order, Payment
from apps.rfqs.models import RFQ
from apps.notifications.utils import notify_deposit_paid


class PayDepositView(ClientRequiredMixin, View):
    def get(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk, quote__rfq__client=request.user)
        return render(request, 'payments/pay.html', {
            'order': order,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        })

    def post(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk, quote__rfq__client=request.user)

        if order.status == Order.DEPOSIT_PAID:
            return redirect('payments:success', order_pk=order.pk)

        reference = f'FORGE-{uuid.uuid4().hex[:12].upper()}'
        amount_kobo = int(order.deposit_amount * 100)  # Paystack uses kobo

        # Initialize Paystack transaction
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        payload = {
            'email': request.user.email,
            'amount': amount_kobo,
            'reference': reference,
            'callback_url': request.build_absolute_uri(f'/payments/success/{order.pk}/'),
            'metadata': {
                'order_id': str(order.pk),
                'rfq_id': str(order.rfq.pk),
                'client_name': request.user.get_full_name(),
            }
        }

        try:
            resp = requests.post(
                'https://api.paystack.co/transaction/initialize',
                headers=headers,
                json=payload,
                timeout=10
            )
            data = resp.json()
            if data.get('status'):
                # Store pending payment record
                Payment.objects.create(
                    order=order,
                    amount=order.deposit_amount,
                    reference=reference,
                    gateway='paystack',
                    status=Payment.PENDING,
                )
                return redirect(data['data']['authorization_url'])
            else:
                return render(request, 'payments/pay.html', {
                    'order': order,
                    'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                    'error': f"Payment initialization failed: {data.get('message', 'Unknown error')}",
                })
        except Exception as e:
            return render(request, 'payments/pay.html', {
                'order': order,
                'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                'error': f"Could not connect to payment gateway. Please try again.",
            })


class PaymentSuccessView(ClientRequiredMixin, View):
    def get(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk, quote__rfq__client=request.user)
        reference = request.GET.get('reference', '')

        if reference and order.status != Order.DEPOSIT_PAID:
            # Verify with Paystack
            headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
            try:
                resp = requests.get(
                    f'https://api.paystack.co/transaction/verify/{reference}',
                    headers=headers,
                    timeout=10
                )
                data = resp.json()
                if data.get('status') and data['data']['status'] == 'success':
                    _confirm_payment(order, reference, data['data'])
            except Exception:
                pass

        return render(request, 'payments/success.html', {'order': order})


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.headers.get('X-Paystack-Signature', '')

        # Verify signature
        expected_sig = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(sig_header, expected_sig):
            return HttpResponse('Invalid signature', status=400)

        event = json.loads(payload)

        if event.get('event') == 'charge.success':
            data = event['data']
            reference = data.get('reference', '')
            order_id = data.get('metadata', {}).get('order_id', '')

            try:
                order = Order.objects.get(pk=order_id)
                if order.status != Order.DEPOSIT_PAID:
                    _confirm_payment(order, reference, data)
            except Order.DoesNotExist:
                pass

        return HttpResponse('OK', status=200)


def _confirm_payment(order, reference, gateway_data):
    """Mark order as deposit paid and update all related records."""
    Payment.objects.filter(reference=reference).update(
        status=Payment.SUCCESS,
        gateway_response=gateway_data,
        paid_at=timezone.now(),
    )
    order.status = Order.DEPOSIT_PAID
    order.save()

    order.rfq.status = RFQ.DEPOSIT_PAID
    order.rfq.save()

    notify_deposit_paid(order)
