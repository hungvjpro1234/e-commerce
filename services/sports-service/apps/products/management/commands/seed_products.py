from django.core.management.base import BaseCommand

from apps.products.models import SportsCategory, SportsProduct


PRODUCTS = [
    ("Nike Training T-Shirt", "Breathable shirt for gym and running.", 28.00, 75, "Nike", "Running", "Polyester", "M", "Unisex"),
    ("Adidas Yoga Mat", "Cushioned mat for yoga and stretching.", 35.00, 42, "Adidas", "Yoga", "Foam", "Standard", "Unisex"),
    ("Decathlon Dumbbell Set", "Adjustable dumbbell set for home workouts.", 89.00, 18, "Decathlon", "Strength Training", "Steel", "20 kg", "Unisex"),
    ("Wilson Basketball", "Indoor and outdoor basketball with strong grip.", 26.00, 40, "Wilson", "Basketball", "Rubber", "Size 7", "Unisex"),
    ("Yonex Badminton Racket", "Lightweight racket for fast swings.", 64.00, 30, "Yonex", "Badminton", "Graphite", "4U", "Unisex"),
    ("Speedo Swim Goggles", "Anti-fog goggles for training sessions.", 18.00, 65, "Speedo", "Swimming", "Silicone", "One Size", "Unisex"),
    ("Under Armour Shorts", "Quick-dry shorts for active workouts.", 32.00, 55, "Under Armour", "Training", "Polyester", "L", "Men"),
    ("Puma Football Boots", "Light boots for firm ground play.", 79.00, 28, "Puma", "Football", "Synthetic", "42", "Men"),
]


class Command(BaseCommand):
    help = "Seed sports products"

    def handle(self, *args, **options):
        cat, _ = SportsCategory.objects.get_or_create(
            name="Sports Equipment",
            defaults={"description": "Training gear and workout accessories"},
        )
        added = 0
        for name, desc, price, stock, brand, sport_type, material, size, target_gender in PRODUCTS:
            if not SportsProduct.objects.filter(name=name).exists():
                SportsProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    sport_type=sport_type,
                    material=material,
                    size=size,
                    target_gender=target_gender,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} sports products."))
