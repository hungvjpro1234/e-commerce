import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent.parent
for path in (CURRENT_DIR, CURRENT_DIR / "shared"):
    path_str = str(path)
    if path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
