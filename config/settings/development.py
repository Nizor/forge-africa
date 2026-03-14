from .base import *
import dj_database_url
from decouple import config as env

DEBUG = True

# If DATABASE_URL is set (CI / Render), use it — otherwise fall back to base.py individual vars
_database_url = env('DATABASE_URL', default='')
if _database_url:
    DATABASES = {
        'default': dj_database_url.parse(_database_url, conn_max_age=600)
    }

# Always use console in development — never attempt real SMTP
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
