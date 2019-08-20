"""
Django settings for myresel project.

Generated by 'django-admin startproject' using Django 1.9.6.
"""

import os
from ipaddress import ip_network

from django.test.runner import DiscoverRunner
from django.utils.translation import ugettext_lazy as _

from myresel.settings_local import *

from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ALLOWED_HOSTS = ['*', 'resel.fr', 'rennes.resel.fr', 'beta.resel.fr', 'beta.rennes.resel.fr']

MAIN_HOST_BREST = 'resel.fr'
MAIN_HOST_RENNES = 'rennes.resel.fr'

PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__))

#
# NETWORKS DEFINITIONS
#
NET_BREST = ip_network("172.22.0.0/16")
NET_RENNES = ip_network("172.23.0.0/16")

NET_BREST_USERS = ip_network("172.22.192.0/19")
NET_BREST_INSCR = ip_network("172.22.224.0/23")
NET_BREST_INSCR_999 = ip_network("172.22.226.0/23")
NET_BREST_GUEST = ip_network("172.22.228.0/23")  # Not used 2017-02-06
NET_BREST_ADM = ip_network("172.22.2.0/23")
NET_BREST_SW = ip_network("172.22.0.0/23")

NET_RENNES_USERS = ip_network("172.23.192.0/19")
NET_RENNES_INSCR = ip_network("172.23.224.0/23")
NET_RENNES_INSCR_999 = ip_network("172.23.226.0/23")
NET_RENNES_GUEST = ip_network("172.23.228.0/23")  # Not used 2017-02-06
NET_RENNES_ADM = ip_network("172.23.2.0/23")
NET_RENNES_SW = ip_network("172.23.0.0/23")

# Number of available ip to insert into the Redis buffer
# The bigger the better but it may be slower
BUFFERED_AV_IPS = 100

# Redis key in which the potential available ips are
REDIS_AV_IPS_KEY = 'av_ips'

## Mails
ADMINS = [
    ('Inscription bot', 'inscription-bot@resel.fr'),
]

## Reminders emails

# Option to totally disable or enable the feature
REMINDERS_ACTIVATED = True
# Do everything but do not send the emails
REMINDER_DRY = False
# remind 1 week before and the eve
REMINDERS_DAYS = [7, 1]
# send an email on the expiration date
REMINDER_EXPIRATION_DAY = True
REMINDER_REDIS_PREFIX = 'myresel_reminders_'
# Number of seconds after which the keys expires
REMINDER_REDIS_EXPIRATON = 60 * 60 * 24 * 30

## Login

LOGIN_URL = '/login'

LOGIN_REDIRECT_URL = '/'

# Inscription zone

INSCRIPTION_ZONE_FALLBACK_URLNAME = 'inscription-zone'

INSCRIPTION_ZONE_ALLOWED_URLNAME = [
    # 'home',
    'login',
    'logout',
    'contact',
    'set_language',
    INSCRIPTION_ZONE_FALLBACK_URLNAME
]

INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE = [
    'gestion-machines',
    'gestion-personnes',
    'tresorerie',
]

#
## Various settings
#

NUMBER_NEWS_IN_HOME = 4
FREE_DURATION = timedelta(days=3*7)

# Cookies settings
SESSION_COOKIE_AGE = 365 * 24 * 60 * 60

# Authentication

AUTHENTICATION_BACKENDS = (
    'django_python3_ldap.auth.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LDAP_AUTH_URL = "ldap://%s:%s" % (LDAP_URL, LDAP_PORT)
LDAP_AUTH_SEARCH_BASE = LDAP_DN_PEOPLE
LDAP_AUTH_OBJECT_CLASS = "genericPerson"
LDAP_AUTH_USER_FIELDS = {
    "username": "uid",
    "first_name": "firstName",
    "last_name": "lastName",
    "email": "mail",
}

# Ckeditor

CKEDITOR_UPLOAD_PATH = 'uploads/'

CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 600,
        'width': 1000,
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'super-banana-split',
    }
}
ICINGA_SERVICES_CACHE_DURATION = 60 * 60
ICINGA_STATUS_CACHE_DURATION = 60
ICINGA_STATUS_CACHE_VERSION = 2

# Languages

LANGUAGES = [
    ('fr', _("Français")),
    ('en', _("Anglais")),
]

MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale/'),
)

# Application definition

INSTALLED_APPS = [
    'modeltranslation',  #Must be before contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_python3_ldap',
    'ckeditor',
    'ckeditor_uploader',
    'phonenumber_field',
    'devices',
    'gestion_personnes',
    'myresel',
    'tresorerie',
    'wiki',
    'pages',
    'django_rq',
    'scheduler',
    'campus',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'myresel.middleware.SimulateProductionNetwork',
    'myresel.middleware.IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAResElAdminSoCheckTheLdapBeforeMiddleware',
    'myresel.middleware.NetworkConfiguration',
]

ROOT_URLCONF = 'myresel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'wiki.context_processors.articles_in_menu',
                'myresel.context_processors.resel_context',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.csrf',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myresel.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
    },
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static_files')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = '/media/'

ADMIN_MEDIA_PREFIX = '/media/adm/'

# Phone numbers

PHONENUMBER_DB_FORMAT = "E164"

PHONENUMBER_DEFAULT_REGION = "FR"


# Redis conf
RQ_QUEUES = {
   'default': {
       'HOST': REDIS_HOST,
       'PORT': REDIS_PORT,
       'DB': REDIS_DB,
       'PASSWORD': REDIS_PASSWORD,
   },
}
RQ_SHOW_ADMIN_LINK = True

# eggdrop settings
EGGDROP_FOLDER = os.path.join(MEDIA_ROOT, 'eggdrop')
EGGDROP_CHANNELS = [
    ('Conversation ResEl', 'resel'),
    ('Conversation Dreamteam', 'dreamteam'),
    ('Conversation CA', 'ca'),
    ('Conversation ResEl2', 'resel2'),
    ('Logs ResEl', 'resellog'),
]
EGGDROP_DEFAULT_CHANNEL = 'resel'


####
# Logging configuration
####

# LOGGERS

PROD_LOGGING_CONF = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(module)s %(process)d %(thread)d : %(message)s'
        },
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(module)s : %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/srv/www/resel.fr/debug.log',
            'formatter': 'simple',
            'encoding': 'utf8',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
            'include_html': True,
        },
        'logstash': {
            'level': 'DEBUG',
            'class': 'logstash.LogstashHandler',
            'host': 'orion',
            'port': 5959,  # Default value: 5959
            'version': 1,
            'message_type': 'django',
            'fqdn': False,  # Fully qualified domain name. Default value: false.
            'tags': None,  # list of tags. Default: None.
        },
    },
    'loggers': {
        'default': {
            'handlers': ['file', 'logstash'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'logstash'],
            'level': 'DEBUG',
            'propagate': True,
        },
        "rq.worker": {
            "handlers": ['file', 'logstash'],
            "level": "DEBUG"
        },

    },
}

# Logger used in a development environment
DEBUG_LOGGING_CONF = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        "rq.worker": {
            "handlers": ['console'],
            "level": "DEBUG"
        },
    },
}

# Profiling configuration
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    'SHOW_COLLAPSED': True,
}

if DEBUG and not TESTING:
    INSTALLED_APPS += ['debug_toolbar',]
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware',] + MIDDLEWARE
    # INTERNAL_IPS = ['10.0.3.1']

elif DEBUG or TESTING:
    LOGGING = DEBUG_LOGGING_CONF
    for queueConfig in RQ_QUEUES.values():
        queueConfig['ASYNC'] = False
else:
    LOGGING = PROD_LOGGING_CONF

if 'test' in sys.argv:
    CAPTCHA_TEST_MODE = True
