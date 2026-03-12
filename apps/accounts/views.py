from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from .forms import ClientRegistrationForm, VendorRegistrationForm, LoginForm
from .models import User
from apps.notifications.utils import send_verification_email


class HomeRedirectView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('/go/')
        if request.user.is_client:
            return redirect('clients:dashboard')
        elif request.user.is_vendor:
            return redirect('vendors:dashboard')
        elif request.user.is_forge_admin:
            return redirect('forge_admin:dashboard')
        return redirect('accounts:login')


class ClientRegisterView(View):
    template_name = 'accounts/register_client.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        form = ClientRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user, request)
            messages.success(request, 'Account created! Please check your email to verify your account.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


class VendorRegisterView(View):
    template_name = 'accounts/register_vendor.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        form = VendorRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = VendorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user, request)
            messages.success(request, 'Vendor account created! Please verify your email before logging in.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


class VerifyEmailView(View):
    def get(self, request, token):
        user = get_object_or_404(User, verification_token=token)
        if user.is_verified:
            messages.info(request, 'Your email is already verified.')
        else:
            user.is_verified = True
            user.save()
            messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_verified:
                messages.warning(request, 'Please verify your email address before logging in.')
                return render(request, self.template_name, {'form': form})
            login(request, user)
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:login')

    def post(self, request):
        logout(request)
        return redirect('accounts:login')


class ResendVerificationView(View):
    def post(self, request):
        email = request.POST.get('email', '').strip()
        if email:
            try:
                user = User.objects.get(email=email)
                if user.is_verified:
                    messages.info(request, 'This account is already verified. Please log in.')
                else:
                    # Regenerate token so old links expire
                    import uuid
                    user.verification_token = uuid.uuid4()
                    user.save()
                    send_verification_email(user, request)
                    messages.success(request, f'Verification email resent to {email}. Please check your inbox.')
            except User.DoesNotExist:
                # Don't reveal if email exists
                messages.success(request, f'If {email} is registered, a verification email has been sent.')
        return redirect('accounts:login')
