from django.core.management.base import BaseCommand

from apps.products.models import MobileCategory, MobileProduct


PRODUCTS = [
    ("iPhone 15 Pro", "Apple's flagship with titanium design.", 1199.00, 30, "Apple", "iOS", 6.1, 4422, 48),
    ("Samsung Galaxy S24 Ultra", "200MP camera with S Pen.", 1399.00, 25, "Samsung", "Android", 6.8, 5000, 200),
    ("Google Pixel 8 Pro", "Best-in-class AI photography.", 999.00, 20, "Google", "Android", 6.7, 5050, 50),
    ("OnePlus 12", "Fast charging flagship killer.", 799.00, 35, "OnePlus", "Android", 6.82, 5400, 50),
    ("Xiaomi 14 Pro", "Top-tier Snapdragon performance.", 899.00, 28, "Xiaomi", "Android", 6.73, 4880, 50),
    ("Sony Xperia 5 V", "Compact flagship with great audio.", 999.00, 15, "Sony", "Android", 6.1, 5000, 52),
    ("OPPO Find X7", "Flagship camera from OPPO.", 749.00, 22, "OPPO", "Android", 6.82, 5000, 50),
    ("Motorola Edge 40 Pro", "Flagship design at mid-range price.", 699.00, 40, "Motorola", "Android", 6.67, 4600, 50),
    ("Nokia G42", "Repairable mid-range smartphone.", 349.00, 60, "Nokia", "Android", 6.56, 5000, 50),
    ("Realme GT5", "Speed-focused phone with fast charging.", 599.00, 45, "Realme", "Android", 6.74, 4600, 50),
    ("Vivo X100 Pro", "Advanced imaging with Zeiss lenses.", 1099.00, 18, "Vivo", "Android", 6.78, 5400, 50),
    ("ASUS ROG Phone 8", "Gaming phone with air triggers.", 1199.00, 12, "ASUS", "Android", 6.78, 6000, 50),
]


class Command(BaseCommand):
    help = "Seed mobile products"

    def handle(self, *args, **options):
        cat, _ = MobileCategory.objects.get_or_create(name="Smartphones", defaults={"description": "All mobile phones"})
        added = 0
        for name, desc, price, stock, brand, os, screen, battery, cam in PRODUCTS:
            if not MobileProduct.objects.filter(name=name).exists():
                MobileProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    operating_system=os,
                    screen_size=screen,
                    battery_mah=battery,
                    camera_mp=cam,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} mobile products."))
