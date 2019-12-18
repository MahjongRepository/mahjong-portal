import os

import dj_database_url

SCHEME = 'https'

AUTH_USER_MODEL = 'account.User'
LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', None)
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', '').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

SITE_ID = 1

INSTALLED_APPS = [
    # it had to be placed before contrib.admin
    'modeltranslation',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    'bootstrap4',
    'haystack',
    'raven.contrib.django.raven_compat',

    'mahjong_portal',
    'club',
    'club.pantheon_games',
    'club.club_games',
    'settings',
    'player',
    'player.tenhou',
    'player.mahjong_soul',
    'tournament',
    'rating',
    'system',
    'system.tournament_admin',
    'account',
    'online',
    'ema'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mahjong_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'system', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',

                'website.context.context'
            ],
        },
    },
]

WSGI_APPLICATION = 'mahjong_portal.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(),
}

if os.environ.get('PANTHEON_DB_URL'):
    DATABASES['pantheon'] = dj_database_url.parse(os.environ.get('PANTHEON_DB_URL'))

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

DATABASE_ROUTERS = ['club.pantheon_games.db_router.PantheonRouter']

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = [
    ['en', 'English'],
    ['ru', 'Russian'],
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

def skip_site_packages_logs(record):
    # This skips the log records that are generated from libraries
    # installed in site packages.
    if 'site-packages' in record.pathname:
        return False
    return True


DJANGO_LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'filters': {
        'skip_site_packages_logs': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_site_packages_logs,
        },
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s django %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console'],
            'filters': ['skip_site_packages_logs'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        }
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    },
}

# https://sentry.io
if os.environ.get('RAVEN_CONFIG'):
    RAVEN_CONFIG = {
        'dsn': os.environ.get('RAVEN_CONFIG'),
    }

TENHOU_WG_URL = 'https://mjv.jp/0/wg/0.js'
TENHOU_LATEST_GAMES_URL = 'http://tenhou.net/sc/raw/list.cgi'
TENHOU_DOWNLOAD_ARCHIVE_URL = 'http://tenhou.net/sc/raw/dat/'

GOOGLE_VERIFICATION_CODE = os.environ.get('GOOGLE_VERIFICATION_CODE', None)
YANDEX_VERIFICATION_CODE = os.environ.get('YANDEX_VERIFICATION_CODE', None)

# online tournaments
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', None)
PANTHEON_URL = os.environ.get('PANTHEON_URL', None)
PANTHEON_EVENT_ID = os.environ.get('PANTHEON_EVENT_ID', None)
PANTHEON_ADMIN_TOKEN = os.environ.get('PANTHEON_ADMIN_TOKEN', None)
TOURNAMENT_ID = os.environ.get('TOURNAMENT_ID', None)
TOURNAMENT_PUBLIC_LOBBY = os.environ.get('TOURNAMENT_PUBLIC_LOBBY', None)
TOURNAMENT_PRIVATE_LOBBY = os.environ.get('TOURNAMENT_PRIVATE_LOBBY', None)
TOURNAMENT_GAME_TYPE = os.environ.get('TOURNAMENT_GAME_TYPE', None)

# mahjong soul statistics fetching
MS_USERNAME = os.environ.get('MS_USERNAME', None)
MS_PASSWORD = os.environ.get('MS_PASSWORD', None)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


# support for non docker installations
try:
    from .settings_local import *
except:
    pass
