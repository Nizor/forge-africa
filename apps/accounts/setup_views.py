"""
One-time setup view for creating the first admin on Render.
REMOVE THIS FILE and its URL entry after first use.
"""
import os
from django.http import HttpResponse, HttpResponseForbidden
from django.views import View
from django.conf import settings
from .models import User


class CreateFirstAdminView(View):
    """
    Protected by a SETUP_SECRET env var.
    Visit: /setup/create-admin/?secret=YOUR_SECRET&email=you@email.com&password=yourpass
    """
    def get(self, request):
        # Must not run in production without the secret
        secret = os.environ.get('SETUP_SECRET', '')
        if not secret:
            return HttpResponseForbidden('SETUP_SECRET env var not set.')

        provided = request.GET.get('secret', '')
        if provided != secret:
            return HttpResponseForbidden('Invalid secret.')

        email = request.GET.get('email', '').strip()
        password = request.GET.get('password', '').strip()

        if not email or not password:
            return HttpResponse(
                '<p>Missing params. Use: ?secret=X&email=Y&password=Z</p>',
                status=400
            )

        if len(password) < 8:
            return HttpResponse('<p>Password must be at least 8 characters.</p>', status=400)

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            return HttpResponse(
                f'<p>⚠️ User <strong>{email}</strong> already exists '
                f'(role={user.role}, is_staff={user.is_staff}).</p>'
                f'<p>If this is your admin, you can log in at /accounts/login/</p>'
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            role=User.ADMIN,
            is_staff=True,
            is_verified=True,
        )

        return HttpResponse(f'''
            <h2>✅ Admin created successfully</h2>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Role:</strong> {user.role}</p>
            <p><a href="/accounts/login/">→ Go to Login</a></p>
            <hr>
            <p style="color:red;"><strong>IMPORTANT:</strong> Remove the /setup/ URL from
            config/urls.py and delete apps/accounts/setup_views.py before going to production.</p>
        ''')
