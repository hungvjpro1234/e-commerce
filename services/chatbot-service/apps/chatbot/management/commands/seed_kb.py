from django.core.management.base import BaseCommand

from apps.chatbot.kb_service import seed_static_kb


class Command(BaseCommand):
    help = "Seed the chatbot knowledge base with static policies and FAQ documents."

    def handle(self, *args, **options):
        self.stdout.write("Seeding static KB (policies + FAQ)...")
        docs, chunks = seed_static_kb()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {docs} documents, {chunks} chunks written."
            )
        )
