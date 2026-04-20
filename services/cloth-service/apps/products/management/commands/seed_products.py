from django.core.management.base import BaseCommand

from apps.products.models import ClothCategory, ClothProduct


PRODUCTS = [
    ("Essential White Tee", "Classic cotton tee for everyday wear.", 19.99, 120, "S,M,L,XL", "Cotton 100%", "White", "Unisex"),
    ("Slim Fit Black Jeans", "Modern slim-fit denim in deep black.", 59.99, 75, "30", "Denim", "Black", "Male"),
    ("Floral Summer Dress", "Light floral print dress perfect for summer.", 44.99, 60, "S", "Chiffon", "Multicolor", "Female"),
    ("Streetwear Hoodie", "Oversized hoodie with kangaroo pocket.", 55.00, 90, "M", "Fleece", "Grey", "Unisex"),
    ("Linen Beach Shirt", "Relaxed linen shirt for warm days.", 39.99, 50, "L", "Linen", "Beige", "Male"),
    ("Yoga Leggings", "High-waist compression leggings.", 35.00, 110, "M", "Spandex", "Navy", "Female"),
    ("Cargo Shorts", "Multi-pocket cargo shorts.", 29.99, 85, "L", "Cotton", "Olive", "Male"),
    ("Knit Sweater", "Warm cable-knit pullover sweater.", 69.99, 40, "M", "Wool Blend", "Cream", "Unisex"),
    ("Running Jacket", "Lightweight windbreaker for outdoor running.", 89.99, 35, "L", "Polyester", "Red", "Unisex"),
    ("Denim Jacket", "Classic washed denim jacket.", 79.99, 45, "M", "Denim", "Blue", "Unisex"),
    ("Formal Blazer", "Slim fit blazer for business occasions.", 119.99, 25, "M", "Polyester Blend", "Charcoal", "Male"),
    ("Flare Skirt", "Boho-style midi skirt with elastic waist.", 38.00, 55, "S", "Viscose", "Floral", "Female"),
    ("Polo Shirt", "Classic pique polo shirt.", 34.99, 95, "L", "Pique Cotton", "Navy", "Male"),
    ("Bomber Jacket", "Urban bomber jacket with ribbed cuffs.", 98.00, 30, "M", "Nylon", "Black", "Unisex"),
]


class Command(BaseCommand):
    help = "Seed cloth products"

    def handle(self, *args, **options):
        cat, _ = ClothCategory.objects.get_or_create(name="General Apparel", defaults={"description": "All cloth items"})
        added = 0
        for name, desc, price, stock, size, material, color, gender in PRODUCTS:
            if not ClothProduct.objects.filter(name=name).exists():
                ClothProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    size=size,
                    material=material,
                    color=color,
                    gender=gender,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} cloth products."))
