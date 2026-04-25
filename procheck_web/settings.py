"""
Django settings for procheck_web project.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# Use environment variables for security in production, fallback to local key
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-930rcv=fdx7b0=(3yr#3tgw^dh8w!+quh)*=0a3k$@4mm3j-b&')

# Turn off DEBUG in production for security, keep it True locally
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allow all hosts so Render can serve the site
ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'main',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # ADDED: WhiteNoise for serving static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'procheck_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'procheck_web.wsgi.application'


# Database
# Connects to Neon.tech using the DATABASE_URL environment variable on Render, 
# and falls back to your local PostgreSQL setup on your computer.
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://procheck_admin:4314@localhost:5432/procheck_db',
        conn_max_age=600
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# ADDED: This tells Django WHERE to gather all files for Render
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ADDED: This tells Django to use WhiteNoise to compress and serve files efficiently
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Auth Redirects
LOGIN_REDIRECT_URL = 'dashboard_redirect' 
LOGOUT_REDIRECT_URL = 'login'