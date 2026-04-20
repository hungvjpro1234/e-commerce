from django.core.management.base import BaseCommand

from apps.recommendations.models import RecommendationArtifact
from apps.recommendations.training import train_and_save_model


class Command(BaseCommand):
    help = "Train the model_behavior artifact from behavior-service data."

    def handle(self, *args, **options):
        result = train_and_save_model()
        RecommendationArtifact.objects.update_or_create(
            name="model_behavior",
            defaults={
                "artifact_path": result["artifact_path"],
                "metadata": result,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Trained model_behavior at {result['artifact_path']}"))
