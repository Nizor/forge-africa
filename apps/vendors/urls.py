app_name = 'vendors'
from django.urls import path
from . import views
urlpatterns = [
    path('dashboard/', views.VendorDashboardView.as_view(), name='dashboard'),
    path('profile/', views.VendorProfileView.as_view(), name='profile'),
    path('rfqs/', views.VendorRFQListView.as_view(), name='rfq_list'),
    path('rfqs/<uuid:pk>/bid/', views.BidCreateView.as_view(), name='bid_create'),
    path('bids/', views.VendorBidListView.as_view(), name='bid_list'),
    path('orders/', views.VendorOrdersView.as_view(), name='orders'),
]
