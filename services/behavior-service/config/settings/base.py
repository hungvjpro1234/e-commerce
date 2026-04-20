from shared.common.django_settings import build_base_settings, build_postgres_db_settings
from shared.common.env import get_env


globals().update(
    build_base_settings(
        service_name="behavior-service",
        installed_apps=["apps.behavior.apps.BehaviorConfig"],
    )
)

DATABASES = build_postgres_db_settings("BEHAVIOR")

CLOTH_SERVICE_URL = get_env("CLOTH_SERVICE_URL", "http://cloth-service:8000")
LAPTOP_SERVICE_URL = get_env("LAPTOP_SERVICE_URL", "http://laptop-service:8000")
MOBILE_SERVICE_URL = get_env("MOBILE_SERVICE_URL", "http://mobile-service:8000")
ACCESSORY_SERVICE_URL = get_env("ACCESSORY_SERVICE_URL", "http://accessory-service:8000")
BEAUTY_SERVICE_URL = get_env("BEAUTY_SERVICE_URL", "http://beauty-service:8000")
GAMING_SERVICE_URL = get_env("GAMING_SERVICE_URL", "http://gaming-service:8000")
