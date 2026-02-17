"""
Management command untuk membuat superuser admin
Usage: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from myauth.models import User


class Command(BaseCommand):
    help = 'Membuat superuser admin dengan username "admin" dan password "12345"'

    def handle(self, *args, **options):
        username = 'admin'
        password = '12345'
        email = 'admin@example.com'

        # Cek apakah user sudah ada
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User dengan username "{username}" sudah ada!')
            )
            # Update password jika user sudah ada
            user = User.objects.get(username=username)
            user.set_password(password)
            user.role = 'admin'
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            if not user.show_password:
                user.show_password = password
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Password untuk user "{username}" telah diupdate!')
            )
        else:
            # Buat user baru
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin',
                show_password=password,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" berhasil dibuat!')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nLogin dengan:\n'
                f'Username: {username}\n'
                f'Password: {password}'
            )
        )

