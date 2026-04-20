from shared.common.django_settings import build_base_settings, build_postgres_db_settings


globals().update(
    build_base_settings(
        service_name="behavior-service",
        installed_apps=[
            "apps.events.apps.EventsConfig",
        ],
    )
)

DATABASES = build_postgres_db_settings("BEHAVIOR")
