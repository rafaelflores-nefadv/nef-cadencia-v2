"""
Production settings for NEF Cadência.
Security-hardened configuration for production deployment.
"""

from .base import *
import os

# ------------------------------------------------------------------
# Security - Production (CRITICAL)
# ------------------------------------------------------------------

from django.core.exceptions import ImproperlyConfigured

# SECRET_KEY must be set in environment - no default for production
SECRET_KEY = env("SECRET_KEY", default=None)

# Debug MUST be False in production
DEBUG = False

# ALLOWED_HOSTS must be explicitly set
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# ------------------------------------------------------------------
# Critical Environment Variables Validation
# ------------------------------------------------------------------

CRITICAL_ENV_VARS = {
    "SECRET_KEY": SECRET_KEY,
    "ALLOWED_HOSTS": ALLOWED_HOSTS,
    "DB_NAME": env("DB_NAME", default=None),
    "DB_USER": env("DB_USER", default=None),
    "DB_PASSWORD": env("DB_PASSWORD", default=None),
    "DB_HOST": env("DB_HOST", default=None),
}

# Validate all critical variables are set
missing_vars = [var for var, value in CRITICAL_ENV_VARS.items() if not value]
if missing_vars:
    raise ImproperlyConfigured(
        f"The following critical environment variables are not set: {', '.join(missing_vars)}. "
        f"Production deployment requires all critical variables to be configured."
    )

# Validate SECRET_KEY is not a default/insecure value
INSECURE_SECRET_KEYS = [
    "change-me-in-production",
    "django-insecure",
    "your-secret-key-here",
    "secret",
    "secretkey",
]
if any(insecure in SECRET_KEY.lower() for insecure in INSECURE_SECRET_KEYS):
    raise ImproperlyConfigured(
        "SECRET_KEY appears to be a default/insecure value. "
        "Generate a secure key using: "
        "python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
    )

# Validate SECRET_KEY length
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        f"SECRET_KEY must be at least 50 characters long (current: {len(SECRET_KEY)})"
    )

# Validate ALLOWED_HOSTS is not using localhost/127.0.0.1
if any(host in ["localhost", "127.0.0.1", "0.0.0.0"] for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS contains localhost/127.0.0.1 which is not secure for production. "
        "Use your actual domain names."
    )

# ------------------------------------------------------------------
# HTTPS and Security Headers
# ------------------------------------------------------------------

# Force HTTPS redirect
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

# Proxy configuration (for nginx/load balancer)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# CSRF trusted origins (for AJAX requests behind proxy)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[]
)

# ------------------------------------------------------------------
# Database - Production
# ------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=600),
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 seconds
        },
    }
}

# ------------------------------------------------------------------
# Cache - Production (Redis)
# ------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
        },
        "KEY_PREFIX": "nef_cadencia",
        "TIMEOUT": 300,
    }
}

# Use cache for sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# ------------------------------------------------------------------
# Email - Production
# ------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default=None)
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default=None)
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default=None)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=None)
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# Email timeout
EMAIL_TIMEOUT = 10

# Validate email configuration
EMAIL_REQUIRED_VARS = {
    "EMAIL_HOST": EMAIL_HOST,
    "EMAIL_HOST_USER": EMAIL_HOST_USER,
    "EMAIL_HOST_PASSWORD": EMAIL_HOST_PASSWORD,
    "DEFAULT_FROM_EMAIL": DEFAULT_FROM_EMAIL,
}

missing_email_vars = [var for var, value in EMAIL_REQUIRED_VARS.items() if not value]
if missing_email_vars:
    import warnings
    warnings.warn(
        f"Email configuration incomplete. Missing: {', '.join(missing_email_vars)}. "
        f"Email functionality will not work properly.",
        RuntimeWarning
    )

# ------------------------------------------------------------------
# Logging - Production
# ------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": env("LOG_FILE", default="/var/log/nef-cadencia/django.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 10,
            "formatter": "json",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": env("ERROR_LOG_FILE", default="/var/log/nef-cadencia/error.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 10,
            "formatter": "json",
            "level": "ERROR",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ------------------------------------------------------------------
# Static Files - Production
# ------------------------------------------------------------------

# Static files served by WhiteNoise or nginx
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# ------------------------------------------------------------------
# Admin
# ------------------------------------------------------------------

# Admin emails for error notifications
ADMINS = [
    (name.strip(), email.strip())
    for admin in env.list("ADMINS", default=[])
    for name, email in [admin.split(":")]
]

MANAGERS = ADMINS

# ------------------------------------------------------------------
# Session Security
# ------------------------------------------------------------------

SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=3600)  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = "nef_sessionid"
CSRF_COOKIE_NAME = "nef_csrftoken"

# ------------------------------------------------------------------
# File Uploads
# ------------------------------------------------------------------

FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# ------------------------------------------------------------------
# Middleware - Production additions
# ------------------------------------------------------------------

# Add security middleware if using WhiteNoise
# MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ------------------------------------------------------------------
# Template - Production
# ------------------------------------------------------------------

# Remove debug context processor in production
TEMPLATES[0]["OPTIONS"]["context_processors"] = [
    cp for cp in TEMPLATES[0]["OPTIONS"]["context_processors"]
    if cp != "django.template.context_processors.debug"
]

# ------------------------------------------------------------------
# Performance
# ------------------------------------------------------------------

# Connection pooling
CONN_MAX_AGE = 600

# Template caching
if not DEBUG:
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        ),
    ]

# ------------------------------------------------------------------
# OpenAI - Production validation
# ------------------------------------------------------------------

# Validate OpenAI API key format
if OPENAI_API_KEY:
    if not OPENAI_API_KEY.startswith("sk-"):
        raise ImproperlyConfigured(
            "OPENAI_API_KEY appears to be invalid. OpenAI API keys should start with 'sk-'"
        )
    if len(OPENAI_API_KEY) < 20:
        raise ImproperlyConfigured(
            f"OPENAI_API_KEY appears to be too short (length: {len(OPENAI_API_KEY)})"
        )
else:
    import warnings
    warnings.warn(
        "OPENAI_API_KEY is not set. Assistant features will not work.",
        RuntimeWarning
    )
