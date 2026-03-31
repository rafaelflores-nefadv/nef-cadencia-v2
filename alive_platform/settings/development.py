"""
Development settings for NEF Cadencia.
Optimized for local development with helpful debugging tools.
"""

from .base import *
from django.core.exceptions import ImproperlyConfigured
import warnings

# ------------------------------------------------------------------
# Security - Development
# ------------------------------------------------------------------

# SECRET_KEY for development only - NEVER use in production
SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-dev-key-change-in-production-12345678901234567890",
)

# Debug mode enabled for development
DEBUG = env.bool("DEBUG", default=True)

# Hosts allowed for local/LAN development
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# ------------------------------------------------------------------
# Database - Development
# ------------------------------------------------------------------


def _sqlite_database_config():
    sqlite_name = env("SQLITE_DB_NAME", default="db.sqlite3")
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / sqlite_name,
        }
    }


def _can_connect_to_postgres():
    try:
        import psycopg  # type: ignore

        connection = psycopg.connect(
            dbname=DATABASES["default"]["NAME"],
            user=DATABASES["default"]["USER"],
            password=DATABASES["default"]["PASSWORD"],
            host=DATABASES["default"]["HOST"],
            port=DATABASES["default"]["PORT"],
            connect_timeout=2,
        )
        connection.close()
        return True
    except Exception:
        return False


DEV_DATABASE_ENGINE = env("DEV_DATABASE_ENGINE", default="postgres").strip().lower()

if DEV_DATABASE_ENGINE in {"sqlite", "sqlite3"}:
    DATABASES = _sqlite_database_config()
elif DEV_DATABASE_ENGINE in {"postgres", "postgresql"}:
    fallback_enabled = env.bool("DEV_POSTGRES_FALLBACK_TO_SQLITE", default=True)
    if fallback_enabled and not _can_connect_to_postgres():
        warnings.warn(
            "Could not connect to PostgreSQL in development. Falling back to local SQLite (db.sqlite3).",
            RuntimeWarning,
        )
        DATABASES = _sqlite_database_config()
else:
    raise ImproperlyConfigured(
        "Invalid DEV_DATABASE_ENGINE. Use 'postgres' or 'sqlite'."
    )

# ------------------------------------------------------------------
# Email - Development (Console backend)
# ------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
DEFAULT_FROM_EMAIL = "noreply@localhost"

# ------------------------------------------------------------------
# Cache - Development (Local memory cache)
# ------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# ------------------------------------------------------------------
# Logging - Development
# ------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Show SQL queries in console (optional)
if env.bool("SHOW_SQL", default=False):
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

# ------------------------------------------------------------------
# Security - Disabled for local development
# ------------------------------------------------------------------

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# ------------------------------------------------------------------
# Session
# ------------------------------------------------------------------

SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_SAVE_EVERY_REQUEST = False
