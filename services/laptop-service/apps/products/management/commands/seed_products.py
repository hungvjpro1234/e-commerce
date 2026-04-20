from django.core.management.base import BaseCommand

from apps.products.models import LaptopCategory, LaptopProduct


PRODUCTS = [
    ("MacBook Air M3", "Ultra-thin laptop with Apple M3 chip.", 1299.00, 20, "Apple", "Apple M3", 8, 256, 13.6),
    ("Dell XPS 15", "Premium 15-inch OLED display laptop.", 1899.00, 15, "Dell", "Intel Core i9", 32, 1000, 15.6),
    ("Lenovo ThinkPad X1 Carbon", "Business ultrabook with long battery life.", 1499.00, 18, "Lenovo", "Intel Core i7", 16, 512, 14.0),
    ("ASUS ZenBook 14", "Compact and powerful everyday laptop.", 799.00, 30, "ASUS", "AMD Ryzen 7", 16, 512, 14.0),
    ("HP Spectre x360", "2-in-1 convertible laptop with OLED touch.", 1599.00, 12, "HP", "Intel Core i7", 16, 512, 14.0),
    ("Acer Swift 3", "Lightweight laptop with great battery.", 649.00, 40, "Acer", "AMD Ryzen 5", 8, 256, 14.0),
    ("MSI Gaming GS66", "High-performance gaming laptop.", 2199.00, 10, "MSI", "Intel Core i9", 32, 1000, 15.6),
    ("Razer Blade 15", "Sleek gaming laptop with 4K display.", 2499.00, 8, "Razer", "Intel Core i7", 16, 512, 15.6),
    ("Surface Laptop 5", "Elegant Surface design with Alcantara keyboard.", 1299.00, 22, "Microsoft", "Intel Core i5", 8, 256, 13.5),
    ("Samsung Galaxy Book3", "Versatile laptop with AMOLED display.", 999.00, 25, "Samsung", "Intel Core i7", 16, 512, 15.6),
    ("LG Gram 17", "Ultra-lightweight 17-inch laptop.", 1599.00, 14, "LG", "Intel Core i7", 16, 1000, 17.0),
    ("Chromebook Flex 5", "Affordable 2-in-1 Chromebook.", 399.00, 50, "Lenovo", "Intel Core i3", 8, 128, 13.3),
]


class Command(BaseCommand):
    help = "Seed laptop products"

    def handle(self, *args, **options):
        cat, _ = LaptopCategory.objects.get_or_create(name="General Laptops", defaults={"description": "All laptop types"})
        added = 0
        for name, desc, price, stock, brand, cpu, ram, storage, display in PRODUCTS:
            if not LaptopProduct.objects.filter(name=name).exists():
                LaptopProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    cpu=cpu,
                    ram_gb=ram,
                    storage_gb=storage,
                    display_size=display,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} laptop products."))
