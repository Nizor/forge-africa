"""
Import vendors from a CSV file exported from Airtable.
Sends each vendor a password reset / welcome email.

Usage:
    python manage.py import_vendors --file vendors.csv
    python manage.py import_vendors --file vendors.csv --dry-run

Expected CSV columns (case-insensitive):
    first_name, last_name, email, company_name, phone, address, city, state

Optional columns:
    description, years_in_business
"""
import csv
import uuid
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = 'Import vendors from Airtable CSV and send welcome/reset emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, required=True,
            help='Path to CSV file exported from Airtable'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview what would be imported without saving anything'
        )
        parser.add_argument(
            '--send-emails', action='store_true', default=True,
            help='Send welcome emails to imported vendors (default: True)'
        )

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.vendors.models import VendorProfile
        from apps.rfqs.models import ServiceCategory

        filepath = options['file']
        dry_run = options['dry_run']

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'File not found: {filepath}'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN — nothing will be saved ===\n'))

        created = 0
        skipped = 0
        errors = 0

        with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            # Normalise column names to lowercase
            rows = []
            for row in reader:
                rows.append({k.lower().strip(): v.strip() for k, v in row.items()})

            self.stdout.write(f'\nFound {len(rows)} rows in CSV\n')

            for i, row in enumerate(rows, 1):
                email = row.get('email', '').strip().lower()

                if not email:
                    self.stdout.write(self.style.WARNING(f'  Row {i}: No email — skipping'))
                    skipped += 1
                    continue

                # Check if already exists
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.WARNING(f'  Row {i}: {email} already exists — skipping'))
                    skipped += 1
                    continue

                first_name = row.get('first_name', '') or row.get('firstname', '') or 'Vendor'
                last_name  = row.get('last_name', '')  or row.get('lastname', '')  or ''
                company    = row.get('company_name', '') or row.get('company', '') or row.get('business_name', '') or f"{first_name}'s Company"
                phone      = row.get('phone', '') or row.get('phone_number', '') or row.get('mobile', '')
                address    = row.get('address', '') or row.get('business_address', '') or 'Lagos, Nigeria'
                city       = row.get('city', '') or 'Lagos'
                state      = row.get('state', '') or 'Lagos'
                description = row.get('description', '') or row.get('bio', '')
                years      = row.get('years_in_business', '') or row.get('years', '')

                self.stdout.write(f'  Row {i}: {email} — {first_name} {last_name} ({company})')

                if dry_run:
                    continue

                try:
                    # Generate a temporary random password — they'll reset it
                    temp_password = get_random_string(16)

                    # Create user
                    user = User.objects.create_user(
                        email=email,
                        password=temp_password,
                        first_name=first_name,
                        last_name=last_name,
                        role=User.VENDOR,
                        is_verified=True,  # Pre-verify since they're known vendors
                    )

                    # Create vendor profile
                    profile = VendorProfile.objects.create(
                        user=user,
                        company_name=company,
                        phone=phone,
                        address=address,
                        city=city,
                        state=state,
                        description=description,
                        years_in_business=int(years) if years and years.isdigit() else None,
                        is_verified=True,  # Pre-verified vendors
                    )

                    # Generate password reset token
                    reset_token = self._generate_reset_token(user)

                    # Send welcome email
                    self._send_welcome_email(user, reset_token)

                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Created and email sent'))

                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'    ✗ Error: {e}'))

        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN COMPLETE'))
            self.stdout.write(f'Would create: {len(rows) - skipped} vendors')
            self.stdout.write(f'Would skip:   {skipped} (already exist or no email)')
        else:
            self.stdout.write(self.style.SUCCESS(f'Import complete'))
            self.stdout.write(f'Created:  {created}')
            self.stdout.write(f'Skipped:  {skipped}')
            self.stdout.write(f'Errors:   {errors}')
        self.stdout.write('=' * 50 + '\n')

    def _generate_reset_token(self, user):
        """Generate a password reset token using Django's built-in token generator."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token

    def _send_welcome_email(self, user, reset_token):
        """Send welcome email with password set link."""
        uid, token = reset_token
        reset_url = f"{settings.SITE_URL}/accounts/reset/{uid}/{token}/"

        subject = "Welcome to Forge Africa — Set Your Password"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #0F172A; padding: 25px; text-align: center;">
                <h1 style="color: #F97316; margin: 0; font-size: 24px;">FORGE AFRICA</h1>
                <p style="color: #94A3B8; margin: 5px 0 0; font-size: 14px;">Manufacturing RFQ Platform</p>
            </div>
            <div style="padding: 35px; background: #f9f9f9;">
                <h2 style="color: #0F172A;">Welcome, {user.first_name}! 👋</h2>
                <p style="color: #374151; line-height: 1.7;">
                    We've created a Forge Africa vendor account for <strong>{user.vendor_profile.company_name}</strong>.
                    You're already verified and ready to start bidding on manufacturing RFQs.
                </p>
                <p style="color: #374151; line-height: 1.7;">
                    Click the button below to set your password and access your dashboard:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="display: inline-block; background: #F97316; color: white;
                              padding: 16px 32px; border-radius: 8px; text-decoration: none;
                              font-weight: bold; font-size: 16px;">
                        Set My Password & Login →
                    </a>
                </div>
                <div style="background: white; border-left: 4px solid #F97316; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #374151; font-size: 14px;">
                        <strong>What you can do on Forge Africa:</strong><br>
                        ✅ Browse and bid on manufacturing RFQs<br>
                        ✅ Receive guaranteed deposit before starting work<br>
                        ✅ Build your reputation with every delivery
                    </p>
                </div>
                <p style="color: #6B7280; font-size: 13px;">
                    This link expires in 72 hours. If you didn't expect this email,
                    please contact us at <a href="mailto:{settings.ADMIN_EMAIL}">{settings.ADMIN_EMAIL}</a>
                </p>
            </div>
            <div style="background: #0F172A; padding: 15px; text-align: center;">
                <p style="color: #64748B; font-size: 12px; margin: 0;">
                    © 2025 Forge Africa · Lagos, Nigeria ·
                    <a href="{settings.SITE_URL}" style="color: #F97316;">forgeafrica.africa</a>
                </p>
            </div>
        </div>
        """

        from apps.notifications.utils import send_email
        send_email(
            user.email,
            subject,
            f'Welcome to Forge Africa! Set your password here: {reset_url}',
            html
        )
