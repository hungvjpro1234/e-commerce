from django.core.management.base import BaseCommand

from apps.products.models import GamingCategory, GamingProduct


PRODUCTS = [
    ("Razer BlackWidow V4", "Mechanical keyboard with tactile switches.", 179.00, 26, "Razer", "PC", "USB-C", "Yes", 24),
    ("SteelSeries Arctis Nova 7", "Wireless gaming headset with long battery life.", 169.00, 22, "SteelSeries", "PC / PlayStation", "2.4GHz + Bluetooth", "No", 24),
    ("Sony DualSense Controller", "Responsive controller with adaptive triggers.", 69.00, 48, "Sony", "PlayStation 5", "Bluetooth / USB-C", "No", 12),
    ("Logitech G502 X Lightspeed", "Wireless gaming mouse with HERO sensor.", 139.00, 34, "Logitech", "PC", "Lightspeed Wireless", "Yes", 24),
    ("HyperX QuadCast S", "RGB USB microphone for streaming and voice chat.", 149.00, 20, "HyperX", "PC", "USB", "Yes", 24),
    ("Nintendo Switch OLED", "Portable console with vibrant OLED screen.", 349.00, 16, "Nintendo", "Switch", "Wi-Fi", "No", 12),
    ("Elgato Stream Deck MK.2", "Customizable control pad for creators and streamers.", 149.00, 18, "Elgato", "PC / Mac", "USB-C", "No", 24),
    ("ASUS TUF Gaming Monitor", "165Hz monitor for immersive gaming.", 239.00, 14, "ASUS", "PC / Console", "HDMI / DisplayPort", "No", 24),
]


class Command(BaseCommand):
    help = "Seed gaming products"

    def handle(self, *args, **options):
        cat, _ = GamingCategory.objects.get_or_create(
            name="Gaming Gear",
            defaults={"description": "Gaming peripherals and entertainment devices"},
        )
        added = 0
        for name, desc, price, stock, brand, platform, connectivity, rgb_support, warranty_months in PRODUCTS:
            if not GamingProduct.objects.filter(name=name).exists():
                GamingProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    platform=platform,
                    connectivity=connectivity,
                    rgb_support=rgb_support,
                    warranty_months=warranty_months,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} gaming products."))
