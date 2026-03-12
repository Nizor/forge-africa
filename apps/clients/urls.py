app_name = 'clients'
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('dashboard/', views.ClientDashboardView.as_view(), name='dashboard'),
    path('rfqs/', views.RFQListView.as_view(), name='rfq_list'),
    path('rfq/new/', views.RFQCreateView.as_view(), name='rfq_create'),
    path('rfq/<uuid:pk>/', views.RFQDetailView.as_view(), name='rfq_detail'),
    path('rfq/<uuid:pk>/quote/', views.QuoteReviewView.as_view(), name='quote_review'),
    path('rfq/<uuid:pk>/accept/', views.QuoteAcceptView.as_view(), name='quote_accept'),
    path('orders/', views.OrderListView.as_view(), name='orders'),
]
