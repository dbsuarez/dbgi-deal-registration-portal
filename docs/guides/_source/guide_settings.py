"""Settings for capturing guide screenshots: the normal debug settings on a throwaway database."""

from pathlib import Path

from config.settings import *  # noqa: F403
from config.settings import DATABASES

DATABASES["default"]["NAME"] = Path(__file__).resolve().parent / "guide-capture.sqlite3"
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
