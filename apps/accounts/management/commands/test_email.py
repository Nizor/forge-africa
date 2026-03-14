from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email via SendGrid HTTP API'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, required=True)

    def handle(self, *args, **options):
        to_email = options['to']

        self.stdout.write('\n=== Forge Africa Email Diagnostics ===\n')
        self.stdout.write(f'DEFAULT_FROM_EMAIL : {settings.DEFAULT_FROM_EMAIL}')

        key = settings.SENDGRID_API_KEY
        if not key:
            self.stdout.write(self.style.ERROR('SENDGRID_API_KEY : NOT SET — check .env'))
            return

        self.stdout.write(f'SENDGRID_API_KEY   : {key[:10]}...{key[-4:]} (len={len(key)})')
        self.stdout.write(f'\nSending via HTTP API to: {to_email}\n')

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content, MimeType

            sg = SendGridAPIClient(key)
            mail = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=to_email,
                subject='Forge Africa — Email Test',
            )
            mail.content = [
                Content(MimeType.text, 'Email test from Forge Africa. It is working!'),
                Content(MimeType.html, '''
                    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;">
                        <div style="background:#E85D04;padding:20px;text-align:center;">
                            <h1 style="color:white;margin:0;">FORGE AFRICA</h1>
                        </div>
                        <div style="padding:30px;background:#f9f9f9;">
                            <h2>Email is working!</h2>
                            <p>Your SendGrid HTTP API integration is configured correctly.</p>
                        </div>
                    </div>
                '''),
            ]

            response = sg.send(mail)
            self.stdout.write(self.style.SUCCESS(
                f'✅ Sent! Status: {response.status_code}\n'
                f'   Check inbox: {to_email}\n'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {e}\n'))
            self.stdout.write('Checklist:')
            self.stdout.write('  1. SENDGRID_API_KEY correct? → sendgrid.com → Settings → API Keys')
            self.stdout.write('  2. API key has "Mail Send" Full Access?')
            self.stdout.write('  3. DEFAULT_FROM_EMAIL is a verified sender?')
            self.stdout.write('     → sendgrid.com → Settings → Sender Authentication')
            self.stdout.write('  4. SendGrid account fully activated?\n')
