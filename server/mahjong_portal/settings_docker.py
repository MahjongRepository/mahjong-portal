from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mahjong_portal',
        'HOST': 'db',
        'USER': 'mahjong_portal',
        'PASSWORD': 'password',
    }
}
