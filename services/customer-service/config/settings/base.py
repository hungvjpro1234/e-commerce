from shared.common.django_settings import build_base_settings, build_postgres_db_settings
from shared.common.env import get_env


globals().update(
    build_base_settings(
        service_name="customer-service",
        installed_apps=[
            "apps.customers.apps.CustomersConfig",
            "apps.cart.apps.CartConfig"
        ],
    )
)

DATABASES = build_postgres_db_settings("CUSTOMER")

BEHAVIOR_SERVICE_URL = get_env("BEHAVIOR_SERVICE_URL", "http://behavior-service:8000")
