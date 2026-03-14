from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SendGrid is working'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, required=True, help='Recipient email address')

    def handle(self, *args, **options):
        to_email = options['to']

        self.stdout.write('\n=== Forge Africa Email Diagnostics ===\n')
        self.stdout.write(f'Active EMAIL_BACKEND : {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST           : {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT           : {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_HOST_USER      : {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL   : {settings.DEFAULT_FROM_EMAIL}')
        key = settings.SENDGRID_API_KEY
        if key:
            self.stdout.write(f'SENDGRID_API_KEY     : {key[:10]}...{key[-4:]} (length={len(key)})')
        else:
            self.stdout.write(self.style.ERROR('SENDGRID_API_KEY     : NOT SET'))
            return

        self.stdout.write(f'\nSending test email to: {to_email}')
        self.stdout.write('Forcing SMTP backend for this test...\n')

        try:
            # Force SMTP directly — bypasses whatever EMAIL_BACKEND is set in settings
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host='smtp.sendgrid.net',
                port=587,
                username='apikey',
                password=settings.SENDGRID_API_KEY,
                use_tls=True,
                fail_silently=False,
            )

            send_mail(
                subject='Forge Africa — Email Test',
                message='This is a test email from Forge Africa. SendGrid is working.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message='''
                <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
                    <div style="background: #E85D04; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">FORGE AFRICA</h1>
                    </div>
                    <div style="padding: 30px; background: #f9f9f9;">
                        <h2 style="color: #1A1A2E;">Email is working!</h2>
                        <p>Your SendGrid integration is configured correctly.</p>
                    </div>
                </div>
                ''',
                connection=connection,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'\n✅ Sent to {to_email} — check inbox and spam.\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Failed: {e}\n'))
            self.stdout.write('Troubleshooting checklist:')
            self.stdout.write('  1. API key correct? → sendgrid.com → Settings → API Keys')
            self.stdout.write('  2. API key has "Mail Send" Full Access permission?')
            self.stdout.write('  3. DEFAULT_FROM_EMAIL is a verified sender in SendGrid?')
            self.stdout.write('     → SendGrid → Settings → Sender Authentication')
            self.stdout.write('  4. SendGrid account fully activated (not pending review)?')
            self.stdout.write(f'\n  Full error: {e}\n')
