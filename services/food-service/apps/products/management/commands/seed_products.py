from django.core.management.base import BaseCommand
from datetime import timedelta

from django.utils import timezone

from apps.products.models import FoodCategory, FoodProduct


PRODUCTS = [
    ("Lay's Classic Chips", "Crispy potato chips for everyday snacking.", 2.50, 200, "Lay's", 150, "Original", 180, "No"),
    ("Oatly Oat Milk", "Plant-based oat drink for coffee and cereal.", 4.50, 85, "Oatly", 1000, "Original", 120, "Yes"),
    ("Nescafe Gold", "Instant coffee with rich aroma.", 8.00, 90, "Nescafe", 200, "Classic", 365, "No"),
    ("Heinz Baked Beans", "Ready-to-eat baked beans in tomato sauce.", 3.20, 110, "Heinz", 415, "Tomato", 300, "No"),
    ("Calbee Granola", "Nutritious breakfast cereal with dried fruit.", 6.80, 70, "Calbee", 500, "Fruit", 240, "No"),
    ("TH True Milk", "Fresh milk enriched with nutrients.", 1.80, 160, "TH True Milk", 180, "Less Sugar", 90, "No"),
    ("Kind Almond Bar", "Nut bar with wholesome ingredients.", 2.20, 140, "Kind", 40, "Honey Almond", 240, "Yes"),
    ("Coca-Cola Zero Sugar", "Zero sugar sparkling beverage.", 1.20, 300, "Coca-Cola", 330, "Cola", 270, "No"),
]


class Command(BaseCommand):
    help = "Seed food products"

    def handle(self, *args, **options):
        cat, _ = FoodCategory.objects.get_or_create(
            name="Food & Drinks",
            defaults={"description": "Snacks, beverages, and ready-to-eat items"},
        )
        added = 0
        for name, desc, price, stock, brand, weight_g, flavor, expiry_offset_days, is_organic in PRODUCTS:
            if not FoodProduct.objects.filter(name=name).exists():
                FoodProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    weight_g=weight_g,
                    flavor=flavor,
                    expiry_date=timezone.now().date() + timedelta(days=expiry_offset_days),
                    is_organic=is_organic,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} food products."))
