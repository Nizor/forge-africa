from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from apps.accounts.decorators import VendorRequiredMixin
from apps.rfqs.models import RFQ, ServiceCategory
from apps.bids.models import Bid, BidAttachment
from apps.vendors.models import VendorProfile
from . import forms


class VendorDashboardView(VendorRequiredMixin, View):
    def get(self, request):
        profile = VendorProfile.objects.filter(user=request.user).first()
        my_bids_qs = Bid.objects.filter(vendor=request.user).select_related('rfq__category').order_by('-created_at')

        if profile and profile.service_categories.exists():
            open_rfqs_qs = RFQ.objects.filter(
                category__in=profile.service_categories.all(),
                status=RFQ.BIDDING_OPEN
            ).exclude(
                bids__vendor=request.user
            ).select_related('category').order_by('-created_at')
        else:
            open_rfqs_qs = RFQ.objects.none()

        stats = {
            'total_bids': my_bids_qs.count(),
            'selected': my_bids_qs.filter(status=Bid.SELECTED).count(),
            'pending': my_bids_qs.filter(status__in=[Bid.SUBMITTED, Bid.UNDER_REVIEW]).count(),
            'open_rfqs': open_rfqs_qs.count(),
        }
        return render(request, 'vendors/dashboard.html', {
            'profile': profile,
            'my_bids': my_bids_qs[:5],
            'open_rfqs': open_rfqs_qs[:5],
            'stats': stats,
        })


class VendorProfileView(VendorRequiredMixin, View):
    template_name = 'vendors/profile.html'

    def get(self, request):
        profile = VendorProfile.objects.filter(user=request.user).first()
        form = forms.VendorProfileForm(instance=profile)
        return render(request, self.template_name, {'form': form, 'profile': profile})

    def post(self, request):
        profile = VendorProfile.objects.filter(user=request.user).first()
        form = forms.VendorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            vendor_profile = form.save(commit=False)
            vendor_profile.user = request.user
            vendor_profile.save()
            form.save_m2m()
            messages.success(request, 'Profile updated successfully.')
            return redirect('vendors:profile')
        return render(request, self.template_name, {'form': form, 'profile': profile})


class VendorRFQListView(VendorRequiredMixin, View):
    def get(self, request):
        profile = VendorProfile.objects.filter(user=request.user).first()
        rfqs = RFQ.objects.none()
        if profile:
            rfqs = RFQ.objects.filter(
                category__in=profile.service_categories.all(),
                status=RFQ.BIDDING_OPEN
            ).order_by('-created_at')
        return render(request, 'vendors/rfq_list.html', {'rfqs': rfqs, 'profile': profile})


class BidCreateView(VendorRequiredMixin, View):
    template_name = 'vendors/bid_create.html'

    def get(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk, status=RFQ.BIDDING_OPEN)
        existing_bid = Bid.objects.filter(rfq=rfq, vendor=request.user).first()
        form = forms.BidForm(instance=existing_bid)
        return render(request, self.template_name, {'rfq': rfq, 'form': form, 'existing_bid': existing_bid})

    def post(self, request, pk):
        rfq = get_object_or_404(RFQ, pk=pk, status=RFQ.BIDDING_OPEN)
        existing_bid = Bid.objects.filter(rfq=rfq, vendor=request.user).first()
        form = forms.BidForm(request.POST, request.FILES, instance=existing_bid)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.rfq = rfq
            bid.vendor = request.user
            bid.status = Bid.SUBMITTED
            bid.save()
            files = request.FILES.getlist('attachments')
            for f in files:
                BidAttachment.objects.create(bid=bid, file=f, filename=f.name)
            action = 'updated' if existing_bid else 'submitted'
            messages.success(request, f'Bid {action} successfully!')
            return redirect('vendors:dashboard')
        return render(request, self.template_name, {'rfq': rfq, 'form': form})


class VendorBidListView(VendorRequiredMixin, View):
    def get(self, request):
        bids = Bid.objects.filter(vendor=request.user).select_related('rfq').order_by('-created_at')
        return render(request, 'vendors/bid_list.html', {'bids': bids})
    
class VendorOrdersView(VendorRequiredMixin, View):
    def get(self, request):
        from django.conf import settings
        from apps.orders.models import Order
        orders = Order.objects.filter(
            quote__selected_bid__vendor=request.user,
            status__in=[Order.DEPOSIT_PAID, Order.IN_PROGRESS, Order.COMPLETED]
        ).select_related(
            'quote__rfq__category',
            'quote__rfq__client',
            'quote__selected_bid'
        ).order_by('-created_at')

        return render(request, 'vendors/orders.html', {
            'orders': orders,
            'admin_email': settings.ADMIN_EMAIL,
        })
