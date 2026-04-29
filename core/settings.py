# Reload triggered at 2026-04-19 19:40
"""
Django settings for core project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-it-now')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# 🔥 แก้ตรงนี้
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    
    # แอปพลิเคชันของคุณ
    'research', 
    
# Reload triggered at 2026-04-19 19:40
"""
Django settings for core project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-it-now')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# 🔥 แก้ตรงนี้
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    
    # แอปพลิเคชันของคุณ
    'research', 
    
    # ระบบลบไฟล์ขยะอัตโนมัติ
    'django_cleanup.apps.CleanupConfig', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # 🔥 เพิ่ม whitenoise สำหรับ static บน Render
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Allow iframes from the same origin (needed for PDF preview)
X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True


# --- Static files ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 🔥 เพิ่มบรรทัดนี้ (สำคัญสำหรับ Render)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- Media files ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- Login / Logout Settings ---
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
if os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = f"RETC Academic Portal <{EMAIL_HOST_USER}>"
else:
    # สำหรับทดสอบ: อีเมลจะแสดงใน Console ของ VS Code ไม่ต้องใช้เน็ต
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# --- Cloudinary Storage for Permanent PDF Files ---
_cloudinary_url = os.getenv('CLOUDINARY_URL')
if _cloudinary_url:
    CLOUDINARY_STORAGE = {
        'CLOUDINARY_URL': _cloudinary_url
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
