from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create a Forge Africa admin (staff) user'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
        parser.add_argument('--first-name', type=str, default='Admin')
        parser.add_argument('--last-name', type=str, default='User')

    def handle(self, *args, **options):
        email = options['email']
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists.'))
            return

        user = User.objects.create_user(
            email=email,
            password=options['password'],
            first_name=options['first_name'],
            last_name=options['last_name'],
            role=User.ADMIN,
            is_staff=True,
            is_verified=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'✓ Admin user created: {user.get_full_name()} ({user.email})'
        ))
