app_name = 'forge_admin'
from django.urls import path
from . import views
urlpatterns = [
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('rfqs/', views.AdminRFQListView.as_view(), name='rfq_list'),
    path('rfqs/<uuid:pk>/', views.AdminRFQDetailView.as_view(), name='rfq_detail'),
    path('rfqs/<uuid:pk>/approve/', views.AdminRFQApproveView.as_view(), name='rfq_approve'),
    path('rfqs/<uuid:pk>/reject/', views.AdminRFQRejectView.as_view(), name='rfq_reject'),
    path('rfqs/<uuid:pk>/bids/', views.AdminBidReviewView.as_view(), name='bid_review'),
    path('rfqs/<uuid:pk>/select-bid/<uuid:bid_id>/', views.AdminSelectBidView.as_view(), name='select_bid'),
    path('rfqs/<uuid:pk>/send-quote/', views.AdminSendQuoteView.as_view(), name='send_quote'),
    path('rfqs/<uuid:pk>/update-status/', views.AdminUpdateRFQStatusView.as_view(), name='update_rfq_status'),
    path('vendors/', views.AdminVendorListView.as_view(), name='vendor_list'),
    path('vendors/<int:pk>/verify/', views.AdminVendorVerifyView.as_view(), name='vendor_verify'),
    path('settings/', views.AdminSettingsView.as_view(), name='settings'),
]
