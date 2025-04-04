from django.core.management.base import BaseCommand
from time_tracking.models import CustomUser
from django.contrib.auth.hashers import make_password
import os

class Command(BaseCommand):
    help = 'Creates the initial admin user'

    def handle(self, *args, **kwargs):
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            self.stdout.write(
                self.style.ERROR('ADMIN_PASSWORD environment variable not set')
            )
            return

        try:
            if not CustomUser.objects.filter(username="admin.timex").exists():
                admin = CustomUser.objects.create(
                    username="admin.timex",
                    password=make_password(admin_password),
                    first_name="Admin",
                    last_name="Timex",
                    email="iosif.gogolos@pdr-team.de",
                    user_type="ADMIN",
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created admin user: {admin.username}')
                )
            else:
                admin = CustomUser.objects.get(username="admin.iosif")
                admin.set_password(admin_password)
                admin.is_staff = True
                admin.is_superuser = True
                admin.save()
                self.stdout.write(
                    self.style.SUCCESS('Updated existing admin user')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create/update admin user: {str(e)}')
            )

        try:
            if not CustomUser.objects.filter(username="admin.timex").exists():
                admin = CustomUser.objects.create(
                    username="admin.timex",
                    password=make_password(admin_password),
                    first_name="Admin",
                    last_name="Timex",
                    email="iosif.gogolos@pdr-team.de",
                    user_type="ADMIN",
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created admin user: {admin.username}')
                )
            else:
                admin = CustomUser.objects.get(username="admin.iosif")
                admin.set_password(admin_password)
                admin.is_staff = True
                admin.is_superuser = True
                admin.save()
                self.stdout.write(
                    self.style.SUCCESS('Updated existing admin user')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create/update admin user: {str(e)}')
            )