from django.core.management.base import BaseCommand

from apps.products.models import BeautyCategory, BeautyProduct


PRODUCTS = [
    ("La Roche-Posay Effaclar Cleanser", "Gentle cleanser for oily and acne-prone skin.", 19.00, 70, "La Roche-Posay", "Oily skin", 200, 24, "France"),
    ("CeraVe Moisturizing Cream", "Ceramide-rich cream for dry skin.", 22.00, 75, "CeraVe", "Dry skin", 340, 24, "USA"),
    ("Anessa Perfect UV Sunscreen", "High-protection sunscreen for daily use.", 29.00, 50, "Anessa", "All skin types", 60, 18, "Japan"),
    ("Maybelline Fit Me Foundation", "Lightweight liquid foundation with natural finish.", 14.00, 90, "Maybelline", "Combination skin", 30, 24, "USA"),
    ("Laneige Lip Sleeping Mask", "Overnight lip care with berry scent.", 21.00, 65, "Laneige", "All skin types", 20, 24, "South Korea"),
    ("The Ordinary Niacinamide 10% + Zinc 1%", "Serum to improve skin texture and oil balance.", 12.00, 110, "The Ordinary", "Oily skin", 30, 24, "Canada"),
    ("Innisfree Green Tea Seed Serum", "Hydrating serum with green tea extract.", 24.00, 55, "Innisfree", "Normal skin", 80, 24, "South Korea"),
    ("Dove Body Wash", "Moisturizing body wash for daily care.", 9.00, 120, "Dove", "Sensitive skin", 550, 18, "Germany"),
]


class Command(BaseCommand):
    help = "Seed beauty products"

    def handle(self, *args, **options):
        cat, _ = BeautyCategory.objects.get_or_create(
            name="Beauty & Skincare",
            defaults={"description": "Skincare and makeup essentials"},
        )
        added = 0
        for name, desc, price, stock, brand, skin_type, volume_ml, expiry_months, origin_country in PRODUCTS:
            if not BeautyProduct.objects.filter(name=name).exists():
                BeautyProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    brand=brand,
                    skin_type=skin_type,
                    volume_ml=volume_ml,
                    expiry_months=expiry_months,
                    origin_country=origin_country,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} beauty products."))
