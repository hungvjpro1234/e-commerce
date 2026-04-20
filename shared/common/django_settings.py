from pathlib import Path

from shared.common.env import get_env


def build_base_settings(*, service_name, installed_apps, extra_rest_permissions=None):
    base_dir = Path(__file__).resolve().parents[2]
    default_permissions = extra_rest_permissions or [
        "rest_framework.permissions.AllowAny"
    ]

    return {
        "BASE_DIR": base_dir,
        "SECRET_KEY": get_env("DJANGO_SECRET_KEY", "change-me"),
        "DEBUG": get_env("DJANGO_DEBUG", True, bool),
        "ALLOWED_HOSTS": ["*"],
        "INSTALLED_APPS": [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "rest_framework",
            *installed_apps,
        ],
        "MIDDLEWARE": [
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ],
        "ROOT_URLCONF": "config.urls",
        "TEMPLATES": [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            }
        ],
        "WSGI_APPLICATION": "config.wsgi.application",
        "LANGUAGE_CODE": "en-us",
        "TIME_ZONE": "UTC",
        "USE_I18N": True,
        "USE_TZ": True,
        "STATIC_URL": "static/",
        "DEFAULT_AUTO_FIELD": "django.db.models.BigAutoField",
        "JWT_SECRET_KEY": get_env("JWT_SECRET_KEY", "change-me-too"),
        "INTERNAL_SERVICE_TOKEN": get_env(
            "INTERNAL_SERVICE_TOKEN", "internal-token-for-local-dev"
        ),
        "SERVICE_NAME": service_name,
        "REST_FRAMEWORK": {
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "shared.common.auth.JWTAuthentication",
                "shared.common.auth.InternalServiceAuthentication",
            ],
            "DEFAULT_PERMISSION_CLASSES": default_permissions,
        },
    }


def build_postgres_db_settings(prefix):
    db_name = get_env(f"{prefix}_DB_NAME")
    if not db_name:
        base_dir = Path(__file__).resolve().parents[2]
        service_slug = prefix.lower()
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": base_dir / f"{service_slug}.sqlite3",
            }
        }
    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": get_env(f"{prefix}_DB_USER"),
            "PASSWORD": get_env(f"{prefix}_DB_PASSWORD"),
            "HOST": get_env(f"{prefix}_DB_HOST"),
            "PORT": get_env(f"{prefix}_DB_PORT", "5432"),
        }
    }
