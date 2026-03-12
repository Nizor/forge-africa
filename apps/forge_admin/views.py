from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils import timezone
from django.db.models import Count, Sum
from apps.accounts.decorators import AdminRequiredMixin
from apps.accounts.models import User
from apps.rfqs.models import RFQ, ServiceCategory
from apps.bids.models import Bid
from apps.quotes.models import Quote
from apps.orders.models import Order, Payment
from apps.vendors.models import VendorProfile
from apps.notifications.utils import (
    notify_client_rfq_approved, notify_client_rfq_rejected,
    notify_vendors_new_rfq, notify_client_quote_ready
)
from . import forms


class AdminDashboardView(AdminRequiredMixin, View):
    def get(self, request):
        stats = {
            'total_rfqs': RFQ.objects.count(),
            'pending_review': RFQ.objects.filter(status=RFQ.SUBMITTED).count(),
            'active_bidding': RFQ.objects.filter(status=RFQ.BIDDING_OPEN).count(),
            'quotes_pending': RFQ.objects.filter(status=RFQ.BIDDING_CLOSED).count(),
            'total_vendors': User.objects.filter(role=User.VENDOR).count(),
            'verified_vendors': VendorProfile.objects.filter(is_verified=True).count(),
            'total_clients': User.objects.filter(role=User.CLIENT).count(),
            'total_revenue': Payment.objects.filter(status=Payment.SUCCESS).aggregate(
                total=Sum('amount'))['total'] or 0,
        }
        recent_rfqs = RFQ.objects.select_related('client', 'category').order_by('-created_at')[:10]
        return render(request, 'forge_admin/dashboard.html', {
            'stats': stats,
            'recent_rfqs': recent_rfqs,
        })


class AdminRFQListView(AdminRequiredMixin, View):
    def get(self, request):
        rfqs = RFQ.objects.select_related('client', 'category').order_by('-created_at')
        status_filter = request.GET.get('status', '')
        if status_filter:
            rfqs = rfqs.filter(status=status_filter)
        return render(request, 'forge_admin/rfq_list.html', {
            'rfqs': rfqs,
            'status_choices': RFQ.STATUS_CHOICES,
            'current_status': status_filter,
        })


class AdminRFQDetailView(AdminRequiredMixin, View):
    def get(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        bids = rfq.bids.select_related('vendor').order_by('price')
        approve_form = forms.RFQApproveForm(instance=rfq)
        reject_form = forms.RFQRejectForm()
        return render(request, 'forge_admin/rfq_detail.html', {
            'rfq': rfq,
            'bids': bids,
            'approve_form': approve_form,
            'reject_form': reject_form,
        })


class AdminRFQApproveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        form = forms.RFQApproveForm(request.POST, instance=rfq)
        if form.is_valid():
            rfq = form.save(commit=False)
            rfq.status = RFQ.BIDDING_OPEN
            rfq.save()

            # Notify client
            notify_client_rfq_approved(rfq)

            # Find and notify vendors in this category
            vendors_in_category = User.objects.filter(
                role=User.VENDOR,
                vendor_profile__service_categories=rfq.category,
                vendor_profile__is_verified=True,
                is_active=True
            ).distinct()
            notify_vendors_new_rfq(rfq, vendors_in_category)

            messages.success(request, f'RFQ {rfq.short_id} approved and sent to {vendors_in_category.count()} vendor(s).')
        else:
            messages.error(request, 'Invalid form data.')
        return redirect('forge_admin:rfq_detail', pk=pk)


class AdminRFQRejectView(AdminRequiredMixin, View):
    def post(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        form = forms.RFQRejectForm(request.POST)
        if form.is_valid():
            rfq.rejection_reason = form.cleaned_data['rejection_reason']
            rfq.status = RFQ.REJECTED
            rfq.save()
            notify_client_rfq_rejected(rfq)
            messages.success(request, f'RFQ {rfq.short_id} rejected and client notified.')
        return redirect('forge_admin:rfq_detail', pk=pk)


class AdminBidReviewView(AdminRequiredMixin, View):
    def get(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        bids = rfq.bids.select_related('vendor', 'vendor__vendor_profile').order_by('price')
        return render(request, 'forge_admin/bid_review.html', {'rfq': rfq, 'bids': bids})


class AdminSelectBidView(AdminRequiredMixin, View):
    def get(self, request, pk, bid_id):
        rfq = get_object_or_404(RFQ, pk=pk)
        bid = get_object_or_404(Bid, pk=bid_id, rfq=rfq)
        form = forms.SelectBidForm(initial={
            'forge_margin_percentage': 0,
            'final_price': bid.price,
            'deposit_percentage': 30,
            'admin_notes': f'Vendor timeline: {bid.timeline_days} working days.'
        })
        return render(request, 'forge_admin/select_bid.html', {'rfq': rfq, 'bid': bid, 'form': form})

    def post(self, request, pk, bid_id):
        rfq = get_object_or_404(RFQ, pk=pk)
        bid = get_object_or_404(Bid, pk=bid_id, rfq=rfq)
        form = forms.SelectBidForm(request.POST)
        if form.is_valid():
            # Mark all other bids as NOT_SELECTED
            rfq.bids.exclude(pk=bid_id).update(status=Bid.NOT_SELECTED)
            bid.status = Bid.SELECTED
            bid.save()

            # Create or update Quote
            quote, _ = Quote.objects.update_or_create(
                rfq=rfq,
                defaults={
                    'selected_bid': bid,
                    'final_price': form.cleaned_data['final_price'],
                    'forge_margin_percentage': form.cleaned_data.get('forge_margin_percentage') or 0,
                    'deposit_percentage': form.cleaned_data['deposit_percentage'],
                    'admin_notes': form.cleaned_data['admin_notes'],
                }
            )

            rfq.status = RFQ.BIDDING_CLOSED
            rfq.save()

            messages.success(request, f'Bid selected. Review and send quote to client.')
            return redirect('forge_admin:send_quote', pk=pk)
        return render(request, 'forge_admin/select_bid.html', {'rfq': rfq, 'bid': bid, 'form': form})


class AdminSendQuoteView(AdminRequiredMixin, View):
    def get(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        if not hasattr(rfq, 'quote'):
            messages.error(request, 'No quote found for this RFQ.')
            return redirect('forge_admin:rfq_detail', pk=pk)
        return render(request, 'forge_admin/send_quote.html', {'rfq': rfq, 'quote': rfq.quote})

    def post(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        quote = rfq.quote
        quote.sent_to_client_at = timezone.now()
        quote.save()
        rfq.status = RFQ.QUOTE_SENT
        rfq.save()
        notify_client_quote_ready(rfq)
        messages.success(request, f'Quote sent to {rfq.client.get_full_name()}. They have been notified by email.')
        return redirect('forge_admin:rfq_detail', pk=pk)


class AdminVendorListView(AdminRequiredMixin, View):
    def get(self, request):
        vendors = VendorProfile.objects.select_related('user').order_by('-created_at')
        return render(request, 'forge_admin/vendor_list.html', {'vendors': vendors})


class AdminVendorVerifyView(AdminRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(VendorProfile, pk=pk)
        profile.is_verified = not profile.is_verified
        profile.save()
        status = 'verified' if profile.is_verified else 'unverified'
        messages.success(request, f'{profile.company_name} has been {status}.')
        return redirect('forge_admin:vendor_list')


class AdminSettingsView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'forge_admin/settings.html', {
            'categories': ServiceCategory.objects.all(),
            'category_form': forms.ServiceCategoryForm(),
        })

    def post(self, request):
        category_form = forms.ServiceCategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, 'Service category added.')
            return redirect('forge_admin:settings')
        return render(request, 'forge_admin/settings.html', {
            'categories': ServiceCategory.objects.all(),
            'category_form': category_form,
        })


class AdminUpdateRFQStatusView(AdminRequiredMixin, View):
    def post(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk)
        new_status = request.POST.get('status')
        allowed = [RFQ.IN_PROGRESS, RFQ.COMPLETED, RFQ.CANCELLED]
        if new_status in allowed:
            rfq.status = new_status
            rfq.save()
            messages.success(request, f'RFQ status updated to {rfq.get_status_display()}.')
        return redirect('forge_admin:rfq_detail', pk=pk)
