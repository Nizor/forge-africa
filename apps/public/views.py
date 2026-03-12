from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from apps.rfqs.models import RFQ, ServiceCategory
from apps.vendors.models import VendorProfile


class LandingView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        categories = ServiceCategory.objects.filter(is_active=True)
        stats = {
            'rfqs': RFQ.objects.exclude(status='DRAFT').count(),
            'vendors': VendorProfile.objects.filter(is_verified=True).count(),
            'categories': categories.count(),
        }
        return render(request, 'public/landing.html', {
            'categories': categories,
            'stats': stats,
        })


class AboutView(View):
    def get(self, request):
        return render(request, 'public/about.html')


class PublicRFQListView(View):
    def get(self, request):
        rfqs = RFQ.objects.filter(
            status=RFQ.BIDDING_OPEN
        ).select_related('category', 'client').order_by('-created_at')
        categories = ServiceCategory.objects.filter(is_active=True)
        cat_filter = request.GET.get('category', '')
        if cat_filter:
            rfqs = rfqs.filter(category__slug=cat_filter)
        return render(request, 'public/rfq_list.html', {
            'rfqs': rfqs,
            'categories': categories,
            'cat_filter': cat_filter,
        })


class VendorDirectoryView(View):
    def get(self, request):
        vendors = VendorProfile.objects.filter(
            is_verified=True
        ).select_related('user').prefetch_related('service_categories').order_by('company_name')
        categories = ServiceCategory.objects.filter(is_active=True)
        cat_filter = request.GET.get('category', '')
        if cat_filter:
            vendors = vendors.filter(service_categories__slug=cat_filter)
        return render(request, 'public/vendor_directory.html', {
            'vendors': vendors,
            'categories': categories,
            'cat_filter': cat_filter,
        })


class ContactView(View):
    def get(self, request):
        return render(request, 'public/contact.html')

    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            try:
                send_mail(
                    subject=f'[Forge Africa Contact] {subject or "New Message"} — from {name}',
                    message=f'From: {name} <{email}>\n\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "Message sent! We'll get back to you within 24 hours.")
            except Exception:
                messages.error(request, "Couldn't send your message. Please email us directly.")
        else:
            messages.error(request, 'Please fill in all required fields.')
        return render(request, 'public/contact.html')


class RefundPolicyView(View):
    def get(self, request):
        return render(request, 'public/policy_refund.html')


class CancellationPolicyView(View):
    def get(self, request):
        return render(request, 'public/policy_cancellation.html')


class TermsView(View):
    def get(self, request):
        return render(request, 'public/policy_terms.html')


class PrivacyView(View):
    def get(self, request):
        return render(request, 'public/policy_privacy.html')
