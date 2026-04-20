from django.core.management.base import BaseCommand

from apps.products.models import AccessoryCategory, AccessoryProduct


PRODUCTS = [
    ("Sony WH-1000XM5", "Industry-leading noise cancelling headphones.", 399.00, 24, "Sony", "Headphones", "Bluetooth, iOS, Android", "Yes", 24),
    ("Anker 737 Charger", "Fast GaN charger for laptops and phones.", 129.00, 40, "Anker", "Charger", "USB-C PD devices", "No", 18),
    ("Logitech MX Master 3S", "Precision wireless mouse for work and creativity.", 109.00, 35, "Logitech", "Mouse", "Windows, macOS", "Yes", 24),
    ("Apple MagSafe Charger", "Magnetic wireless charger for iPhone.", 49.00, 50, "Apple", "Wireless Charger", "iPhone with MagSafe", "Yes", 12),
    ("Razer Gigantus V2", "Soft gaming mouse pad with smooth glide.", 19.00, 80, "Razer", "Mouse Pad", "Universal", "No", 6),
    ("UGREEN USB-C Hub", "7-in-1 hub with HDMI and card reader.", 59.00, 45, "UGREEN", "Hub", "USB-C laptops and tablets", "No", 12),
    ("Samsung 45W Travel Adapter", "Super fast charger for Samsung devices.", 39.00, 60, "Samsung", "Wall Charger", "USB-C smartphones and tablets", "No", 12),
    ("Baseus Bowie M2s", "Affordable ANC earbuds for daily commute.", 69.00, 55, "Baseus", "Earbuds", "iOS, Android", "Yes", 12),
]


class Command(BaseCommand):
    help = "Seed accessory products"

    def handle(self, *args, **options):
        cat, _ = AccessoryCategory.objects.get_or_create(
            name="Tech Accessories",
            defaults={"description": "Chargers, headphones, mice, and other accessories"},
        )
        added = 0
        for name, desc, price, stock, brand, accessory_type, compatibility, wireless, warranty_months in PRODUCTS:
            if not AccessoryProduct.objects.filter(name=name).exists():
                AccessoryProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    accessory_type=accessory_type,
                    compatibility=compatibility,
                    wireless=wireless,
                    warranty_months=warranty_months,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} accessory products."))
