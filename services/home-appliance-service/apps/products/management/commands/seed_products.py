from django.core.management.base import BaseCommand

from apps.products.models import HomeApplianceCategory, HomeApplianceProduct


PRODUCTS = [
    ("Philips Air Fryer 3000", "Healthy frying with rapid air technology.", 149.00, 18, "Philips", 1400, "4.1 L", "A", "Air Fryer"),
    ("Panasonic Microwave NN-ST34", "Compact microwave oven for quick meals.", 129.00, 14, "Panasonic", 800, "25 L", "A", "Microwave"),
    ("Tefal Electric Kettle", "1.7L kettle with auto shut-off.", 39.00, 40, "Tefal", 2200, "1.7 L", "A", "Electric Kettle"),
    ("Sharp Rice Cooker KS-COM18", "Simple rice cooker for family meals.", 79.00, 20, "Sharp", 700, "1.8 L", "A", "Rice Cooker"),
    ("Dyson V8 Slim", "Cordless vacuum cleaner for quick cleaning.", 429.00, 9, "Dyson", 425, "0.54 L", "A+", "Vacuum Cleaner"),
    ("Xiaomi Smart Fan 2", "Quiet smart standing fan with app control.", 99.00, 26, "Xiaomi", 15, "Standard", "A+", "Fan"),
    ("Sunhouse SHD7721", "Blender for smoothies and sauces.", 49.00, 32, "Sunhouse", 350, "1.25 L", "A", "Blender"),
    ("Bear Mini Grill", "Tabletop grill for indoor cooking.", 69.00, 22, "Bear", 1200, "2 Plates", "A", "Electric Grill"),
]


class Command(BaseCommand):
    help = "Seed home-appliance products"

    def handle(self, *args, **options):
        cat, _ = HomeApplianceCategory.objects.get_or_create(
            name="General Home Appliances",
            defaults={"description": "Kitchen and daily living appliances"},
        )
        added = 0
        for name, desc, price, stock, brand, power_watt, capacity, energy_rating, appliance_type in PRODUCTS:
            if not HomeApplianceProduct.objects.filter(name=name).exists():
                HomeApplianceProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    power_watt=power_watt,
                    capacity=capacity,
                    energy_rating=energy_rating,
                    appliance_type=appliance_type,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} home-appliance products."))
