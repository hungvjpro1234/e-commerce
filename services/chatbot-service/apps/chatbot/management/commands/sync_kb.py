from django.core.management.base import BaseCommand

from apps.chatbot.kb_service import run_full_sync


class Command(BaseCommand):
    help = (
        "Sync the chatbot knowledge base: seed static documents and ingest "
        "products from all catalog services."
    )

    def handle(self, *args, **options):
        self.stdout.write("Running full KB sync (static + products)...")
        result = run_full_sync()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {result['synced_documents']} documents, "
                f"{result['synced_chunks']} chunks in {result['duration_ms']} ms."
            )
        )
