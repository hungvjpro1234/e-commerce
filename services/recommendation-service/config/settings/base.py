from pathlib import Path

from shared.common.django_settings import build_base_settings, build_postgres_db_settings
from shared.common.env import get_env


globals().update(
    build_base_settings(
        service_name="recommendation-service",
        installed_apps=["apps.recommendations.apps.RecommendationsConfig"],
    )
)

DATABASES = build_postgres_db_settings("RECOMMENDATION")

BEHAVIOR_SERVICE_URL = get_env("BEHAVIOR_SERVICE_URL", "http://behavior-service:8000")
MODEL_ARTIFACT_PATH = get_env("RECOMMENDATION_MODEL_ARTIFACT", str(Path(BASE_DIR) / "artifacts" / "model_behavior.pt"))
RECOMMENDATION_TOP_K = int(get_env("RECOMMENDATION_TOP_K", "6"))
