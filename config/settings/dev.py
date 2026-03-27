from . import base

DEBUG = True
ALLOWED_HOSTS = ['*']

# Dev tools
INSTALLED_APPS = base.INSTALLED_APPS + [
    # 'debug_toolbar',
]

# Email backend for dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Caching (Local Memory)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
