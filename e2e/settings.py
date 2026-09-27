"""Local-only settings for the disposable Selenium server and database."""

import os

# Select the SQLite branch before loading the project's configuration.
os.environ["PRODUCTION"] = "False"

from portofolio.settings import *  # noqa: E402,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:"},
    }
}
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
