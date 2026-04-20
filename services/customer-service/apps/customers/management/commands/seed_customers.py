from django.core.management.base import BaseCommand

from apps.customers.models import Customer


class Command(BaseCommand):
    help = "Seed demo customer account"

    def handle(self, *args, **options):
        if Customer.objects.filter(email="customer@example.com").exists():
            self.stdout.write("Customer already exists, skipping.")
            return
        c = Customer(email="customer@example.com", full_name="Demo Customer")
        c.set_password("strongpass123")
        c.save()
        self.stdout.write(self.style.SUCCESS("Created customer: customer@example.com / strongpass123"))
