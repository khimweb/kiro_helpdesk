from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create default admin user if not exists'

    def handle(self, *args, **kwargs):
        username = 'khim'
        password = 'admin1234'

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'User "{username}" already exists.')
            return

        User.objects.create_superuser(
            username=username,
            password=password,
            email='khim@helpdesk.com',
            role='admin',
            first_name='Khim',
        )
        self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created successfully.'))
