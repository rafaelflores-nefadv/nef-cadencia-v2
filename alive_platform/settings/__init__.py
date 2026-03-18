"""
Settings package for NEF Cadência.

Usage:
    Development: DJANGO_SETTINGS_MODULE=alive_platform.settings.development
    Production:  DJANGO_SETTINGS_MODULE=alive_platform.settings.production
    Testing:     DJANGO_SETTINGS_MODULE=alive_platform.settings.test

Default: development (if DJANGO_ENV not set)
"""

import os

# Determine which settings to use based on DJANGO_ENV
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .production import *
elif DJANGO_ENV == 'test':
    from .test import *
else:
    from .development import *
