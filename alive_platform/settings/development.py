"""
Development settings for NEF Cadência.
Optimized for local development with helpful debugging tools.
"""

from .base import *

# ------------------------------------------------------------------
# Security - Development
# ------------------------------------------------------------------

# SECRET_KEY for development only - NEVER use in production
SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-dev-key-change-in-production-12345678901234567890"
)

# Debug mode enabled for development
DEBUG = env.bool("DEBUG", default=True)

# Permissive ALLOWED_HOSTS for local development
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost", "0.0.0.0"])

# ------------------------------------------------------------------
# Database - Development
# ------------------------------------------------------------------

# Development uses default database settings from base.py
# Override if needed:
# DATABASES['default']['NAME'] = 'alive_platform_dev'

# ------------------------------------------------------------------
# Email - Development (Console backend)
# ------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
DEFAULT_FROM_EMAIL = "noreply@localhost"

# ------------------------------------------------------------------
# Cache - Development (Dummy cache)
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

# ------------------------------------------------------------------
# Development Tools
# ------------------------------------------------------------------

# Show SQL queries in console (optional, can be enabled via env var)
if env.bool("SHOW_SQL", default=False):
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

# ------------------------------------------------------------------
# Security - Disabled for local development
# ------------------------------------------------------------------

# HTTPS not required in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# ------------------------------------------------------------------
# CORS - Permissive for local development
# ------------------------------------------------------------------

# If using CORS, allow all origins in development
# CORS_ALLOW_ALL_ORIGINS = True

# ------------------------------------------------------------------
# Static Files - Development
# ------------------------------------------------------------------

# Static files served by Django in development
# No special configuration needed

# ------------------------------------------------------------------
# Session
# ------------------------------------------------------------------

SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_SAVE_EVERY_REQUEST = False
