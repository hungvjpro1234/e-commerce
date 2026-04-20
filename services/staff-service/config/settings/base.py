from shared.common.django_settings import build_base_settings, build_postgres_db_settings


globals().update(
    build_base_settings(
        service_name="staff-service",
        installed_apps=[
            "apps.staff_accounts.apps.StaffAccountsConfig"
        ],
    )
)

DATABASES = build_postgres_db_settings("STAFF")
