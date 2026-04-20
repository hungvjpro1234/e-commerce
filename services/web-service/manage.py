#!/usr/bin/env python
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
for path in (CURRENT_DIR, CURRENT_DIR / "shared"):
    path_str = str(path)
    if path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
