from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.conf import settings
from apps.accounts.decorators import ClientRequiredMixin
from apps.rfqs.models import RFQ, RFQAttachment, ServiceCategory
from apps.orders.models import Order
from apps.notifications.utils import notify_admin_new_rfq
from . import forms


class ClientDashboardView(ClientRequiredMixin, View):
    def get(self, request):
        rfqs = RFQ.objects.filter(client=request.user).order_by('-created_at')
        stats = {
            'total': rfqs.count(),
            'active': rfqs.filter(status__in=[
                RFQ.SUBMITTED, RFQ.APPROVED, RFQ.BIDDING_OPEN,
                RFQ.BIDDING_CLOSED, RFQ.QUOTE_SENT, RFQ.ACCEPTED
            ]).count(),
            'in_progress': rfqs.filter(status=RFQ.IN_PROGRESS).count(),
            'completed': rfqs.filter(status=RFQ.COMPLETED).count(),
        }
        return render(request, 'clients/dashboard.html', {
            'rfqs': rfqs[:10],
            'stats': stats,
        })


class RFQCreateView(ClientRequiredMixin, View):
    template_name = 'clients/rfq_create.html'

    def get(self, request):
        form = forms.RFQForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = forms.RFQForm(request.POST, request.FILES)
        if form.is_valid():
            rfq = form.save(commit=False)
            rfq.client = request.user
            rfq.status = RFQ.SUBMITTED
            rfq.save()

            # Handle multiple file uploads
            files = request.FILES.getlist('attachments')
            for f in files:
                RFQAttachment.objects.create(rfq=rfq, file=f, filename=f.name)

            notify_admin_new_rfq(rfq, request)
            messages.success(request, f'RFQ {rfq.short_id} submitted successfully! We\'ll review it shortly.')
            return redirect('clients:rfq_detail', pk=rfq.pk)
        return render(request, self.template_name, {'form': form})


class RFQDetailView(ClientRequiredMixin, View):
    def get(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk, client=request.user)
        return render(request, 'clients/rfq_detail.html', {'rfq': rfq})


class RFQListView(ClientRequiredMixin, View):
    def get(self, request):
        rfqs = RFQ.objects.filter(client=request.user).order_by('-created_at')
        status_filter = request.GET.get('status', '')
        if status_filter:
            rfqs = rfqs.filter(status=status_filter)
        return render(request, 'clients/rfq_list.html', {
            'rfqs': rfqs,
            'status_choices': RFQ.STATUS_CHOICES,
            'current_status': status_filter,
        })


class QuoteReviewView(ClientRequiredMixin, View):
    def get(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk, client=request.user)
        if not hasattr(rfq, 'quote'):
            messages.warning(request, 'No quote available for this RFQ yet.')
            return redirect('clients:rfq_detail', pk=pk)
        return render(request, 'clients/quote_review.html', {'rfq': rfq, 'quote': rfq.quote})


class QuoteAcceptView(ClientRequiredMixin, View):
    def post(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk, client=request.user)
        if rfq.status != RFQ.QUOTE_SENT:
            messages.error(request, 'This RFQ is not in a state where a quote can be accepted.')
            return redirect('clients:rfq_detail', pk=pk)

        quote = rfq.quote
        # Use the deposit % set by admin at quote time, fall back to platform default
        deposit_pct = quote.deposit_percentage or getattr(settings, 'DEFAULT_DEPOSIT_PERCENTAGE', 30)
        total = quote.final_price
        from decimal import Decimal
        deposit = (Decimal(deposit_pct) / 100) * total

        order, created = Order.objects.get_or_create(
            quote=quote,
            defaults={
                'deposit_percentage': deposit_pct,
                'deposit_amount': deposit,
                'total_amount': total,
                'balance_due': total - deposit,
                'status': Order.PENDING_PAYMENT,
            }
        )

        rfq.status = RFQ.ACCEPTED
        rfq.save()

        messages.success(request, f'Quote accepted! Please complete your deposit payment to begin the project.')
        return redirect('payments:pay_deposit', order_pk=order.pk)


class OrderListView(ClientRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.filter(
            quote__rfq__client=request.user
        ).select_related('quote__rfq').order_by('-created_at')
        return render(request, 'clients/orders.html', {'orders': orders})
