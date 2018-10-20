# SCHEME = 'https'

# LOGOUT_REDIRECT_URL = '/'
# LOGIN_REDIRECT_URL = '/'
# LOGIN_URL = '/login/'

SECRET_KEY = '--SECRET_KEY--'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['--HOST--']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '--DB_NAME--',
        'HOST': '--DB_HOST--',
        'USER': '--DB_USER--',
        'PASSWORD': '--DB_PASSWORD--',
    }
}

# LANGUAGE_CODE = 'en'
# LANGUAGES = [
#     ['en', 'English'],
#     ['ru', 'Russian'],
# ]

# TIME_ZONE = 'UTC'

# YANDEX_METRIKA_ID = None
# GOOGLE_VERIFICATION_CODE = None
# YANDEX_VERIFICATION_CODE = None

# TELEGRAM_TOKEN = None
# PANTHEON_URL = None
# PANTHEON_EVENT_ID = None
# PANTHEON_ADMIN_TOKEN = None

# TENHOU_WG_URL = None
# TENHOU_LATEST_GAMES_URL = None
# TENHOU_DOWNLOAD_ARCHIVE_URL = None
