"""
Test settings for NEF Cadência.
Optimized for running tests with speed and isolation.
"""

from .base import *

# ------------------------------------------------------------------
# Security - Test
# ------------------------------------------------------------------

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# ------------------------------------------------------------------
# Database - Test (In-memory SQLite for speed)
# ------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ------------------------------------------------------------------
# Cache - Test (Dummy cache)
# ------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# ------------------------------------------------------------------
# Email - Test (Memory backend)
# ------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ------------------------------------------------------------------
# Password Hashing - Test (Faster hashing)
# ------------------------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ------------------------------------------------------------------
# Logging - Test (Minimal logging)
# ------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# ------------------------------------------------------------------
# Security - Disabled for tests
# ------------------------------------------------------------------

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# ------------------------------------------------------------------
# Performance - Test optimizations
# ------------------------------------------------------------------

# Disable migrations for faster tests (optional)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()
