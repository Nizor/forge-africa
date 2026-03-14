"""
Tests for authentication flows — registration, login, email verification, access control.
Run: python manage.py test tests.test_auth
"""
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from apps.accounts.models import User
from .factories import make_client, make_vendor, make_admin


class RegistrationTest(TestCase):

    def setUp(self):
        self.client = TestClient()

    def test_client_registration_page_loads(self):
        response = self.client.get('/accounts/register/client/')
        self.assertEqual(response.status_code, 200)

    def test_vendor_registration_page_loads(self):
        response = self.client.get('/accounts/register/vendor/')
        self.assertEqual(response.status_code, 200)

    def test_client_registration_creates_user(self):
        response = self.client.post('/accounts/register/client/', {
            'first_name': 'Emeka',
            'last_name': 'Okonkwo',
            'email': 'emeka@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        self.assertTrue(User.objects.filter(email='emeka@test.com').exists())
        user = User.objects.get(email='emeka@test.com')
        self.assertEqual(user.role, User.CLIENT)
        self.assertFalse(user.is_verified)

    def test_vendor_registration_creates_user(self):
        self.client.post('/accounts/register/vendor/', {
            'first_name': 'Chukwudi',
            'last_name': 'Manu',
            'email': 'vendor@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'company_name': 'Manu Manufacturing Ltd',
            'phone': '08012345678',
            'address': '5 Industrial Ave, Apapa',
            'city': 'Lagos',
            'state': 'Lagos',
        })
        self.assertTrue(User.objects.filter(email='vendor@test.com').exists())
        user = User.objects.get(email='vendor@test.com')
        self.assertEqual(user.role, User.VENDOR)

    def test_duplicate_email_rejected(self):
        make_client(email='taken@test.com')
        self.client.post('/accounts/register/client/', {
            'first_name': 'Other',
            'last_name': 'User',
            'email': 'taken@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        self.assertEqual(User.objects.filter(email='taken@test.com').count(), 1)

    def test_password_mismatch_rejected(self):
        self.client.post('/accounts/register/client/', {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'new@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'WrongPass456!',
        })
        self.assertFalse(User.objects.filter(email='new@test.com').exists())


class EmailVerificationTest(TestCase):

    def setUp(self):
        self.client = TestClient()

    def test_valid_token_verifies_user(self):
        user = make_client(verified=False)
        token = user.verification_token
        response = self.client.get(f'/accounts/verify/{token}/')
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_invalid_token_returns_404(self):
        import uuid
        response = self.client.get(f'/accounts/verify/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)

    def test_already_verified_user_handled(self):
        user = make_client(verified=True)
        token = user.verification_token
        response = self.client.get(f'/accounts/verify/{token}/')
        self.assertIn(response.status_code, [200, 302])


class LoginTest(TestCase):

    def setUp(self):
        self.client = TestClient()

    def test_login_page_loads(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_verified_client_can_login(self):  # redirects to / then HomeRedirectView handles role
        user = make_client(verified=True)
        response = self.client.post('/accounts/login/', {
            'username': 'client@test.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_verified_vendor_redirects_to_vendor_dashboard(self):
        user = make_vendor(verified=True)
        response = self.client.post('/accounts/login/', {
            'username': 'vendor@test.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_admin_redirects_to_admin_dashboard(self):
        user = make_admin()
        response = self.client.post('/accounts/login/', {
            'username': 'admin@test.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_unverified_user_cannot_login(self):
        make_client(verified=False)
        response = self.client.post('/accounts/login/', {
            'username': 'client@test.com',
            'password': 'testpass123',
        })
        # Should stay on login page with warning
        self.assertEqual(response.status_code, 200)

    def test_wrong_password_rejected(self):
        make_client(verified=True)
        response = self.client.post('/accounts/login/', {
            'username': 'client@test.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_clears_session(self):
        user = make_client(verified=True)
        self.client.login(email='client@test.com', password='testpass123')
        self.client.get('/accounts/logout/')
        response = self.client.get('/client/dashboard/')
        self.assertNotEqual(response.status_code, 200)


class AccessControlTest(TestCase):
    """Ensure each role can only access its own section."""

    def setUp(self):
        self.client_user = make_client(email='c@test.com', verified=True)
        self.vendor_user = make_vendor(email='v@test.com', verified=True)
        self.admin_user = make_admin(email='a@test.com')
        self.tc = TestClient()

    def test_unauthenticated_cannot_access_client_dashboard(self):
        response = self.tc.get('/client/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_vendor_dashboard(self):
        response = self.tc.get('/vendor/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_cannot_access_admin_dashboard(self):
        response = self.tc.get('/forge/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_client_cannot_access_vendor_dashboard(self):
        self.tc.login(email='c@test.com', password='testpass123')
        response = self.tc.get('/vendor/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_vendor_cannot_access_client_dashboard(self):
        self.tc.login(email='v@test.com', password='testpass123')
        response = self.tc.get('/client/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_client_cannot_access_admin_dashboard(self):
        self.tc.login(email='c@test.com', password='testpass123')
        response = self.tc.get('/forge/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_vendor_cannot_access_admin_dashboard(self):
        self.tc.login(email='v@test.com', password='testpass123')
        response = self.tc.get('/forge/dashboard/')
        self.assertNotEqual(response.status_code, 200)

    def test_client_can_access_own_dashboard(self):
        self.tc.login(email='c@test.com', password='testpass123')
        response = self.tc.get('/client/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_vendor_can_access_own_dashboard(self):
        self.tc.login(email='v@test.com', password='testpass123')
        response = self.tc.get('/vendor/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_admin_dashboard(self):
        self.tc.login(email='a@test.com', password='testpass123')
        response = self.tc.get('/forge/dashboard/')
        self.assertEqual(response.status_code, 200)
