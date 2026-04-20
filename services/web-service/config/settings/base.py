from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = "web-service-local-secret-key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core.apps.CoreConfig",
    "apps.gateway.apps.GatewayConfig",
    "apps.customer_portal.apps.CustomerPortalConfig",
    "apps.staff_portal.apps.StaffPortalConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.app_context",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_NAME = "ecommerce_web_session"
LOGIN_URL = "/staff/login"
CUSTOMER_LOGIN_URL = "/login"

STAFF_SERVICE_URL = "http://staff-service:8000"
CUSTOMER_SERVICE_URL = "http://customer-service:8000"
CLOTH_SERVICE_URL = "http://cloth-service:8000"
LAPTOP_SERVICE_URL = "http://laptop-service:8000"
MOBILE_SERVICE_URL = "http://mobile-service:8000"
ACCESSORY_SERVICE_URL = "http://accessory-service:8000"
HOME_APPLIANCE_SERVICE_URL = "http://home-appliance-service:8000"
BOOK_SERVICE_URL = "http://book-service:8000"
BEAUTY_SERVICE_URL = "http://beauty-service:8000"
FOOD_SERVICE_URL = "http://food-service:8000"
SPORTS_SERVICE_URL = "http://sports-service:8000"
GAMING_SERVICE_URL = "http://gaming-service:8000"
