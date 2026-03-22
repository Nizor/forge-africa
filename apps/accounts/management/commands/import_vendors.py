"""
Import vendors from a CSV file exported from Airtable.
Sends each vendor a welcome email with password set link.

Usage:
    python manage.py import_vendors --file vendors.csv
    python manage.py import_vendors --file vendors.csv --dry-run
"""
import csv
import os
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = 'Import vendors from Airtable CSV and send welcome emails'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True,
                            help='Path to CSV file')
        parser.add_argument('--dry-run', action='store_true',
                            help='Preview without saving')

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.vendors.models import VendorProfile

        filepath = options['file']
        dry_run = options['dry_run']

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'File not found: {filepath}'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN — nothing will be saved ===\n'))

        created = skipped = errors = 0

        with open(filepath, newline='', encoding='utf-8-sig') as f:
            rows = [{k.lower().strip(): v.strip() for k, v in row.items()}
                    for row in csv.DictReader(f)]

        self.stdout.write(f'\nFound {len(rows)} rows in CSV\n')

        for i, row in enumerate(rows, 1):
            email = row.get('email', '').strip().lower()

            if not email:
                self.stdout.write(self.style.WARNING(f'  Row {i}: No email — skipping'))
                skipped += 1
                continue

            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'  Row {i}: {email} already exists — skipping'))
                skipped += 1
                continue

            first_name  = row.get('first_name', '') or row.get('firstname', '') or 'Vendor'
            last_name   = row.get('last_name', '')  or row.get('lastname', '')  or ''
            company     = (row.get('company_name', '') or row.get('company', '') or
                          row.get('business_name', '') or f"{first_name}'s Company")
            phone       = row.get('phone', '') or row.get('phone_number', '') or row.get('mobile', '')
            address     = row.get('address', '') or row.get('business_address', '') or 'Lagos, Nigeria'
            city        = row.get('city', '') or 'Lagos'
            state       = row.get('state', '') or 'Lagos'
            description = row.get('description', '') or row.get('bio', '')
            years       = row.get('years_in_business', '') or row.get('years', '')

            self.stdout.write(f'  Row {i}: {email} — {first_name} {last_name} ({company})')

            if dry_run:
                continue

            try:
                user = User.objects.create_user(
                    email=email,
                    password=get_random_string(16),
                    first_name=first_name,
                    last_name=last_name,
                    role=User.VENDOR,
                    is_verified=True,
                )

                VendorProfile.objects.create(
                    user=user,
                    company_name=company,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    description=description,
                    years_in_business=int(years) if years and years.isdigit() else None,
                    is_verified=True,
                )

                # Send email directly (no thread — management commands exit before threads complete)
                sent = self._send_welcome_email(user)
                if sent:
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Created — email sent'))
                else:
                    self.stdout.write(self.style.WARNING(f'    ✓ Created — email failed (check SendGrid)'))
                created += 1

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'    ✗ Error: {e}'))

        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE'))
            self.stdout.write(f'Would create: {len(rows) - skipped} vendors')
            self.stdout.write(f'Would skip:   {skipped}')
        else:
            self.stdout.write(self.style.SUCCESS('Import complete'))
            self.stdout.write(f'Created:  {created}')
            self.stdout.write(f'Skipped:  {skipped}')
            self.stdout.write(f'Errors:   {errors}')
        self.stdout.write('=' * 50 + '\n')

    def _send_welcome_email(self, user):
        """Send welcome email directly via SendGrid HTTP API — no threading."""
        from django.conf import settings
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content, MimeType
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.encoding import force_bytes
            from django.utils.http import urlsafe_base64_encode

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.SITE_URL}/accounts/reset/{uid}/{token}/"

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            mail = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=user.email,
                subject='Welcome to Forge Africa — Set Your Password',
            )
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                <div style="background:#0F172A;padding:25px;text-align:center;">
                    <h1 style="color:#F97316;margin:0;font-size:24px;">FORGE AFRICA</h1>
                    <p style="color:#94A3B8;margin:5px 0 0;font-size:14px;">Manufacturing RFQ Platform</p>
                </div>
                <div style="padding:35px;background:#f9f9f9;">
                    <h2 style="color:#0F172A;">Welcome, {user.first_name}! 👋</h2>
                    <p style="color:#374151;line-height:1.7;">
                        We've created a Forge Africa vendor account for
                        <strong>{user.vendor_profile.company_name}</strong>.
                        You're already verified and ready to start bidding on manufacturing RFQs.
                    </p>
                    <p style="color:#374151;line-height:1.7;">
                        Click below to set your password and access your dashboard:
                    </p>
                    <div style="text-align:center;margin:30px 0;">
                        <a href="{reset_url}"
                           style="display:inline-block;background:#F97316;color:white;
                                  padding:16px 32px;border-radius:8px;text-decoration:none;
                                  font-weight:bold;font-size:16px;">
                            Set My Password &amp; Login &rarr;
                        </a>
                    </div>
                    <div style="background:white;border-left:4px solid #F97316;
                                padding:15px;margin:20px 0;border-radius:0 8px 8px 0;">
                        <p style="margin:0;color:#374151;font-size:14px;">
                            <strong>What you can do on Forge Africa:</strong><br>
                            ✅ Browse and bid on manufacturing RFQs<br>
                            ✅ Receive guaranteed deposit before starting work<br>
                            ✅ Build your reputation with every delivery
                        </p>
                    </div>
                    <p style="color:#6B7280;font-size:13px;">
                        This link expires in 72 hours. Questions?
                        Contact <a href="mailto:{settings.ADMIN_EMAIL}">{settings.ADMIN_EMAIL}</a>
                    </p>
                </div>
                <div style="background:#0F172A;padding:15px;text-align:center;">
                    <p style="color:#64748B;font-size:12px;margin:0;">
                        &copy; 2025 Forge Africa &middot; Lagos, Nigeria &middot;
                        <a href="{settings.SITE_URL}" style="color:#F97316;">forgeafrica.africa</a>
                    </p>
                </div>
            </div>
            """
            mail.content = [
                Content(MimeType.text, f'Welcome to Forge Africa! Set your password: {reset_url}'),
                Content(MimeType.html, html),
            ]
            response = sg.send(mail)
            self.stdout.write(f'    → Email status: {response.status_code}')
            return response.status_code == 202

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    → Email error: {e}'))
            return False
