from django.core.management.base import BaseCommand

from apps.products.models import BookCategory, BookProduct


PRODUCTS = [
    ("Atomic Habits", "Practical strategies to build good habits.", 18.00, 120, "James Clear", "Avery", "English", 320, "Self-help"),
    ("Clean Code", "A handbook of agile software craftsmanship.", 35.00, 65, "Robert C. Martin", "Prentice Hall", "English", 464, "Programming"),
    ("Deep Work", "Rules for focused success in a distracted world.", 19.00, 70, "Cal Newport", "Grand Central Publishing", "English", 304, "Productivity"),
    ("Dune", "Epic science fiction saga on Arrakis.", 22.00, 85, "Frank Herbert", "Ace", "English", 688, "Science Fiction"),
    ("The Psychology of Money", "Timeless lessons on wealth and happiness.", 17.00, 95, "Morgan Housel", "Harriman House", "English", 256, "Finance"),
    ("Harry Potter and the Sorcerer's Stone", "Fantasy adventure for all ages.", 16.00, 140, "J.K. Rowling", "Scholastic", "English", 320, "Fantasy"),
    ("Start With Why", "How great leaders inspire everyone to take action.", 20.00, 72, "Simon Sinek", "Portfolio", "English", 256, "Business"),
    ("Sapiens", "A brief history of humankind.", 24.00, 58, "Yuval Noah Harari", "Harper", "English", 498, "History"),
]


class Command(BaseCommand):
    help = "Seed book products"

    def handle(self, *args, **options):
        cat, _ = BookCategory.objects.get_or_create(
            name="General Books",
            defaults={"description": "Books for learning and entertainment"},
        )
        added = 0
        for name, desc, price, stock, author, publisher, language, page_count, genre in PRODUCTS:
            if not BookProduct.objects.filter(name=name).exists():
                BookProduct.objects.create(
                    category=cat,
                    name=name,
                    description=desc,
                    price=price,
                    stock=stock,
                    image_url=f"https://picsum.photos/seed/{name.replace(' ', '')}/400/300",
                    is_active=True,
                    author=author,
                    publisher=publisher,
                    language=language,
                    page_count=page_count,
                    genre=genre,
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {added} book products."))
