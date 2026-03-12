from django.urls import path
from . import views

app_name = 'accounts' 

urlpatterns = [
    path('', views.HomeRedirectView.as_view(), name='home'),
    path('register/client/', views.ClientRegisterView.as_view(), name='register_client'),
    path('register/vendor/', views.VendorRegisterView.as_view(), name='register_vendor'),
    path('verify/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
]
