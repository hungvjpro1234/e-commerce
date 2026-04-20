from shared.common.django_settings import build_base_settings, build_postgres_db_settings
from shared.common.env import get_env


globals().update(
    build_base_settings(
        service_name="chatbot-service",
        installed_apps=[
            "apps.chatbot.apps.ChatbotConfig",
        ],
    )
)

DATABASES = build_postgres_db_settings("CHATBOT")

OPENAI_API_KEY = get_env("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = get_env("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = get_env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
USE_EMBEDDING_RETRIEVAL = get_env("USE_EMBEDDING_RETRIEVAL", False, bool)

GEMINI_API_KEY = get_env("GEMINI_API_KEY", "")
# gemini-2.0-flash đôi khi có quota free tier = 0 trên project; 1.5-flash ổn định hơn
GEMINI_CHAT_MODEL = get_env("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
_raw_fallbacks = get_env("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash-lite,gemini-2.0-flash")
GEMINI_FALLBACK_MODELS = [m.strip() for m in _raw_fallbacks.split(",") if m.strip()]

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

KB_RETRIEVAL_TOP_K = int(get_env("KB_RETRIEVAL_TOP_K", "5"))
CONVERSATION_HISTORY_LIMIT = int(get_env("CONVERSATION_HISTORY_LIMIT", "6"))
