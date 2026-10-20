"""Settings for the test suite only.

`DEBUG` now defaults to off, so the suite opts into the development defaults
before the real settings module is imported. Tests never run with the
production configuration.
"""

import os

os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "pytest-only-insecure-secret")

from .settings import *  # noqa: F403
