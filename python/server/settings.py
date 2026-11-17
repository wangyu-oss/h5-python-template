import os
import sys
from pathlib import Path

from corsheaders.defaults import default_headers
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.getenv('DATA_DIR', ROOT_DIR / 'data'))
load_dotenv(BASE_DIR / '.env')

DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'uploads').mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'logs').mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*'] if DEBUG else [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders',
    'common',
    'accounts',
    'rbac',
    'system',
    'files',
    'notify',
    'pay',
    'track',
    'plugins',
    'jobs',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'common.middleware.ExceptionMiddleware',
    'common.middleware.TraceMiddleware',
    'common.middleware.ApiLogMiddleware',
    'common.middleware.BlacklistMiddleware',
    'common.middleware.RateLimitMiddleware',
    'common.middleware.SignMiddleware',
    'common.middleware.AuthMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'server.urls'
WSGI_APPLICATION = 'server.wsgi.application'
ASGI_APPLICATION = 'server.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': []},
    }
]

DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')
if DB_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'h5'),
            'USER': os.getenv('POSTGRES_USER', 'h5'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'h5'),
            'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
    read_host = os.getenv('DB_READ_HOST', '').strip()
    if read_host:
        DATABASES['replica'] = {
            **DATABASES['default'],
            'HOST': read_host,
            'PORT': os.getenv('DB_READ_PORT', os.getenv('POSTGRES_PORT', '5432')),
        }
        USE_REPLICA = True
    else:
        USE_REPLICA = False
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DATA_DIR / 'app.sqlite3',
            'OPTIONS': {'timeout': 20},
        }
    }
    USE_REPLICA = False

DATABASE_ROUTERS = ['common.dbrouter.ReadReplicaRouter']

REDIS_URL = os.getenv('REDIS_URL', '').strip()
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'h5-template',
        }
    }

AUTH_PASSWORD_VALIDATORS = []
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

origins = [item.strip() for item in os.getenv(
    'CORS_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174',
).split(',') if item.strip()]
CORS_ALLOWED_ORIGINS = origins
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-trace-id',
    'idempotency-key',
    'x-timestamp',
    'x-nonce',
    'x-sign',
    'x-device-id',
]

REFRESH_COOKIE = 'h5_refresh'
USE_CELERY = os.getenv('USE_CELERY', '0') == '1'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {'redact': {'()': 'common.logging.RedactFilter'}},
    'formatters': {
        'std': {'format': '%(asctime)s %(levelname)s %(name)s %(message)s'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'std', 'filters': ['redact']},
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': DATA_DIR / 'logs' / 'app.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'std',
            'encoding': 'utf-8',
            'filters': ['redact'],
        },
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO'},
}

TESTING = 'test' in sys.argv
