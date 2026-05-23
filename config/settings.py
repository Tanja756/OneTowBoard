"""
Django settings for config project.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Добавляем папку apps в путь для импорта приложений как "users", "listings" и т.д.
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# ---------- Продакшен-настройки (менять при деплое) ----------
SITE_NAME = os.environ.get('SITE_NAME', 'Продай или Купи на Раз, Два')
SITE_DESCRIPTION = os.environ.get('SITE_DESCRIPTION', 'Бесплатная доска объявлений: недвижимость, авто, услуги, работа и многое другое')
SITE_KEYWORDS = os.environ.get('SITE_KEYWORDS', 'доска объявлений, бесплатные объявления, купить, продать, недвижимость, авто, работа')
SITE_ADDRESS = os.environ.get('SITE_ADDRESS', '')
SITE_PHONE = os.environ.get('SITE_PHONE', '')
SITE_EMAIL = os.environ.get('SITE_EMAIL', '')
SITE_WORKING_HOURS = os.environ.get('SITE_WORKING_HOURS', '')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-0102030405060-9874-abcd-abcdef012354')

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    'http://localhost'
).split(',')

# --------------------- Конец продакшен-настроек ---------------------

# Google OAuth – можно отключить через .env (ENABLE_GOOGLE_AUTH=False)
ENABLE_GOOGLE_AUTH = os.environ.get('ENABLE_GOOGLE_AUTH', 'True').lower() == 'true'

# Избранное – можно отключить через .env (ENABLE_FAVORITES=False)
ENABLE_FAVORITES = os.environ.get('ENABLE_FAVORITES', 'True').lower() == 'true'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ---------- Приложения ----------
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django_user_agents',
    # Наши приложения
    'users',
    'listings',
    'categories',
    'ratings',
    'search',
    'msgs_app',
]

# Google-авторизация (можно отключить)
if ENABLE_GOOGLE_AUTH:
    INSTALLED_APPS += [
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'allauth.socialaccount.providers.google',
    ]

# ---------- Бекенды аутентификации ----------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
if ENABLE_GOOGLE_AUTH:
    AUTHENTICATION_BACKENDS.append('allauth.account.auth_backends.AuthenticationBackend')

# ---------- Настройки allauth ----------
if ENABLE_GOOGLE_AUTH:
    ACCOUNT_LOGIN_METHODS = {'email', 'username'}
    ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
    ACCOUNT_EMAIL_VERIFICATION = 'optional'
    ACCOUNT_LOGOUT_REDIRECT_URL = 'listings:index'
    LOGIN_REDIRECT_URL = 'listings:index'
    LOGOUT_REDIRECT_URL = 'listings:index'
    LOGIN_URL = '/accounts/login/'
    SOCIALACCOUNT_LOGIN_ON_GET = True
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
        }
    }
    SOCIALACCOUNT_ADAPTER = 'apps.users.adapters.CustomSocialAccountAdapter'
    # ID приложения Google (из .env)
    SOCIAL_AUTH_GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    SOCIAL_AUTH_GOOGLE_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
else:
    # Если Google выключен, используем стандартный URL входа
    LOGIN_URL = '/users/login/'

# ---------- Middleware ----------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    'config.middleware.ProfileCompletionMiddleware',   # всегда проверяем заполненность профиля
    'config.middleware.LastActivityMiddleware',         # обновление last_activity
    'config.middleware.UnreadMessagesMiddleware',       # уведомление о непрочитанных
]

if ENABLE_GOOGLE_AUTH:
    MIDDLEWARE.insert(
        MIDDLEWARE.index('config.middleware.ProfileCompletionMiddleware'),
        'allauth.account.middleware.AccountMiddleware'
    )

# ---------- Остальные настройки ----------
SITE_ID = int(os.environ.get('SITE_ID', 1))

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'categories.context_processors.categories_processor',
                'config.context_processors.site_settings',
                'config.context_processors.user_theme',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

_db_dir = os.environ.get('DJANGO_DB_DIR', os.path.join(BASE_DIR, 'db'))
os.makedirs(_db_dir, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(_db_dir, 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = os.environ.get('TZ', 'Europe/Moscow')
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
_media_root = os.environ.get('DJANGO_MEDIA_ROOT')
MEDIA_ROOT = Path(_media_root) if _media_root else BASE_DIR / 'media'
os.makedirs(MEDIA_ROOT, exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ADMIN_SITE_HEADER = "OneTwoBoard — управление"
ADMIN_SITE_TITLE = "OneTwoBoard Admin"
ADMIN_INDEX_TITLE = "Добро пожаловать в панель управления OneTwoBoard"

# ---------- Почтовые настройки ----------
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', '')
TECH_SUPPORT_EMAIL = os.environ.get('TECH_SUPPORT_EMAIL', '')

# Уведомления техподдержке
NOTIFY_ADMIN_NEW_USER = os.environ.get('NOTIFY_ADMIN_NEW_USER', 'False').lower() == 'true'
NOTIFY_ADMIN_NEW_LISTING = os.environ.get('NOTIFY_ADMIN_NEW_LISTING', 'False').lower() == 'true'

# ---------- Расширенное логирование (опционально) ----------
# Включение: ENABLE_DEBUG_LOGGING=True в .env или переменных окружения
ENABLE_DEBUG_LOGGING = os.environ.get('ENABLE_DEBUG_LOGGING', 'False').lower() == 'true'
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# ---------- Логирование ----------
_handlers = {
    'file_upload': {
        'level': 'DEBUG',
        'class': 'logging.FileHandler',
        'filename': os.path.join(BASE_DIR, 'logs', 'upload.log'),
        'formatter': 'verbose',
    },
    'console': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}

_loggers = {
    'upload': {
        'handlers': ['file_upload', 'console'],
        'level': 'DEBUG',
        'propagate': False,
    },
}

# Если включено расширенное логирование — добавляем debug-логгер
if ENABLE_DEBUG_LOGGING:
    _handlers['file_debug'] = {
        'level': 'DEBUG',
        'class': 'logging.FileHandler',
        'filename': os.path.join(BASE_DIR, 'logs', 'debug.log'),
        'formatter': 'verbose',
    }
    _loggers['debug'] = {
        'handlers': ['file_debug', 'console'],
        'level': 'DEBUG',
        'propagate': False,
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': _handlers,
    'loggers': _loggers,
}
