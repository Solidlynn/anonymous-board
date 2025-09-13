"""
Production settings for anonymous_board project.
"""

import os
from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
# Use a fallback secret key for Railway deployment
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-j$$icw@pcx)vw3+$-wwi-f1veqz-d*u^a$@6fpwlfb1xkynloo')

# SECURITY WARNING: don't run with debug turned on in production!
# Temporarily enable DEBUG to see error details
DEBUG = True

ALLOWED_HOSTS = ['*']  # Railway에서 사용할 도메인 허용

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files serving in production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Additional static files settings for Railway
# Note: STATICFILES_DIRS should not include directories that are also in STATIC_ROOT
if not os.path.exists(BASE_DIR / 'staticfiles'):
    STATICFILES_DIRS = [
        BASE_DIR / 'static',
    ]
else:
    STATICFILES_DIRS = []

# Ensure static files are served correctly
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Redis 설정 (Railway에서 제공하는 Redis 사용)
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    # Redis가 없는 경우 InMemory 채널 레이어 사용
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        },
    }

# 보안 설정
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
