from shared.common.django_settings import build_base_settings, build_postgres_db_settings
from shared.common.env import get_env


globals().update(
    build_base_settings(
        service_name="recommendation-service",
        installed_apps=[
            "apps.recommendations.apps.RecommendationsConfig",
        ],
    )
)

DATABASES = build_postgres_db_settings("RECOMMENDATION")

CLOTH_SERVICE_URL = get_env("CLOTH_SERVICE_URL", "http://cloth-service:8000")
LAPTOP_SERVICE_URL = get_env("LAPTOP_SERVICE_URL", "http://laptop-service:8000")
MOBILE_SERVICE_URL = get_env("MOBILE_SERVICE_URL", "http://mobile-service:8000")
ACCESSORY_SERVICE_URL = get_env("ACCESSORY_SERVICE_URL", "http://accessory-service:8000")
HOME_APPLIANCE_SERVICE_URL = get_env("HOME_APPLIANCE_SERVICE_URL", "http://home-appliance-service:8000")
BOOK_SERVICE_URL = get_env("BOOK_SERVICE_URL", "http://book-service:8000")
BEAUTY_SERVICE_URL = get_env("BEAUTY_SERVICE_URL", "http://beauty-service:8000")
FOOD_SERVICE_URL = get_env("FOOD_SERVICE_URL", "http://food-service:8000")
SPORTS_SERVICE_URL = get_env("SPORTS_SERVICE_URL", "http://sports-service:8000")
GAMING_SERVICE_URL = get_env("GAMING_SERVICE_URL", "http://gaming-service:8000")

RECOMMENDATION_MODEL_ARTIFACT = get_env(
    "RECOMMENDATION_MODEL_ARTIFACT",
    str(BASE_DIR / "services" / "recommendation-service" / "artifacts" / "trained_models" / "model_best.pt"),
)
RECOMMENDATION_TOP_K = get_env("RECOMMENDATION_TOP_K", 6, int)
