from django.core.management.base import BaseCommand

from apps.staff_accounts.models import StaffUser


class Command(BaseCommand):
    help = "Seed demo staff account"

    def handle(self, *args, **options):
        if StaffUser.objects.filter(email="admin@example.com").exists():
            self.stdout.write("Staff admin@example.com already exists, skipping.")
            return
        user = StaffUser(email="admin@example.com", full_name="Store Admin", role="manager")
        user.set_password("strongpass123")
        user.save()
        self.stdout.write(self.style.SUCCESS("Created staff: admin@example.com / strongpass123"))
