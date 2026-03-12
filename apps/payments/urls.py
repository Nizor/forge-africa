app_name = 'payments'
from django.urls import path
from . import views
urlpatterns = [
    path('pay/<uuid:order_pk>/', views.PayDepositView.as_view(), name='pay_deposit'),
    path('success/<uuid:order_pk>/', views.PaymentSuccessView.as_view(), name='success'),
    path('webhook/', views.PaystackWebhookView.as_view(), name='paystack_webhook'),
]
