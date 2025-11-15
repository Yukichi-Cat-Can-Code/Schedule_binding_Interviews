"""
Django settings for interview_scheduler project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-development-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'api',
    'scheduler',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'interview_scheduler.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'interview_scheduler.wsgi.application'

# Database - SQLite for Django admin/auth (instead of Djongo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

from pymongo import MongoClient

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_NAME = os.getenv('MONGODB_DB_NAME', 'schedule_interview') 

try:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    mongodb = mongo_client[MONGODB_NAME]
    print(f"✅ Connected to MongoDB: {MONGODB_NAME}")
except Exception as e:
    print(f"⚠️  MongoDB connection failed: {e}")
    print("   App will use SQLite only. Update MONGODB_URI in .env to use MongoDB.")
    mongodb = None

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True
# Expose filename header for downloads (so frontend can read it)
CORS_EXPOSE_HEADERS = [
    'Content-Disposition',
]

# CSRF - trust local dev frontend
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000').split(',')

# Spectacular Settings (API Documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Interview Scheduler API',
    'DESCRIPTION': 'API for Interview Scheduling with Genetic Algorithm',
    'VERSION': '1.0.0',
}

# Celery Configuration (for async tasks)
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Algorithm Configuration
ALGORITHM_CONFIG = {
    'GA': {
        'POPULATION_SIZE': int(os.getenv('GA_POPULATION_SIZE', 100)),
        'GENERATIONS': int(os.getenv('GA_GENERATIONS', 200)),
        'CROSSOVER_RATE': float(os.getenv('GA_CROSSOVER_RATE', 0.8)),
        'MUTATION_RATE': float(os.getenv('GA_MUTATION_RATE', 0.15)),
        'TOURNAMENT_SIZE': 3,
        'ELITISM_RATE': 0.1,
    },
    'WEIGHTS': {
        'CONFLICT': float(os.getenv('WEIGHT_CONFLICT', 0.4)),
        'IDLE': float(os.getenv('WEIGHT_IDLE', 0.2)),
        'FAIRNESS': float(os.getenv('WEIGHT_FAIRNESS', 0.2)),
        'MATCHING': float(os.getenv('WEIGHT_MATCHING', 0.1)),
        'ROOM': float(os.getenv('WEIGHT_ROOM', 0.1)),
    }
}
