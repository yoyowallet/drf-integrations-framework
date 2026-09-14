"""SQLite settings used for fast migration and compatibility test feedback."""

from example.settings import *  # noqa: F403, I001


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
