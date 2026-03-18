"""
Configurações JWT para autenticação.

Adicione ao settings.py:
from .settings_jwt import *
"""
from datetime import timedelta

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Manter session para admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Simple JWT
SIMPLE_JWT = {
    # Access token expira em 1 hora
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    
    # Refresh token expira em 7 dias
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Rotacionar refresh token ao usar
    'ROTATE_REFRESH_TOKENS': True,
    
    # Blacklist refresh tokens antigos
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Algoritmo de assinatura
    'ALGORITHM': 'HS256',
    
    # Chave de assinatura (usar SECRET_KEY do Django)
    'SIGNING_KEY': None,  # Será preenchido automaticamente
    
    # Claims customizados
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Token no cookie (opcional)
    'AUTH_COOKIE': None,
    
    # Atualizar last_login ao gerar token
    'UPDATE_LAST_LOGIN': True,
}

# Password Hashers (Bcrypt é mais seguro)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',  # Bcrypt (recomendado)
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',        # Fallback
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# CORS (se frontend estiver em domínio diferente)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
