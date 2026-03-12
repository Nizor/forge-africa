from django.urls import path
from . import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('rfqs/', views.PublicRFQListView.as_view(), name='public_rfqs'),
    path('vendors/', views.VendorDirectoryView.as_view(), name='vendor_directory'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('refund-policy/', views.RefundPolicyView.as_view(), name='refund_policy'),
    path('cancellation-policy/', views.CancellationPolicyView.as_view(), name='cancellation_policy'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
]
