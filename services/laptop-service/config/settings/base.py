from shared.common.django_settings import build_base_settings, build_postgres_db_settings


globals().update(
    build_base_settings(
        service_name="laptop-service",
        installed_apps=[
            "apps.products.apps.ProductsConfig"
        ],
    )
)

DATABASES = build_postgres_db_settings("LAPTOP")
