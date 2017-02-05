"""
Django settings for myresel project.

Generated by 'django-admin startproject' using Django 1.9.6.
"""

import os

from django.test.runner import DiscoverRunner
from django.utils.translation import ugettext_lazy as _

from myresel.settings_local import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ALLOWED_HOSTS = ['*', 'resel.fr', 'rennes.resel.fr', 'beta.resel.fr', 'beta.rennes.resel.fr']

MAIN_HOST_BREST = 'resel.fr'
MAIN_HOST_RENNES = 'rennes.resel.fr'

PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__))

# Mails
ADMINS = [
    ('Inscription bot', 'inscription-bot@resel.fr'),
]

# Login

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

NUMBER_NEWS_IN_HOME = 4

#

AUTHENTICATION_BACKENDS = (
    'django_python3_ldap.auth.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LDAP_AUTH_URL = "ldap://%s:%s" % (LDAP_URL, LDAP_PORT)
LDAP_AUTH_USE_TLS = False
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
    'gestion_machines',
    'gestion_personnes',
    'myresel',
    'tresorerie',
    'wiki',
    'pages',
    'django_rq',
    'whoswho',
    'clubs',
]

MIDDLEWARE_CLASSES = [
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
    'myresel.middleware.inscriptionNetworkHandler',
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
    'qos': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_QOS_NAME,
        'USER': DB_QOS_USER,
        'PASSWORD': DB_QOS_PASSWORD,
        'HOST': DB_QOS_HOST,
    }
}
DATABASE_ROUTERS = ['gestion_machines.models.QoSRouter']


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


####
# DIRTY HACK FOR QoS DATABASE
####

# During tests, the Django ORM would not create the unmanaged models
# This Hack makes it possible :
# See : https://gist.github.com/raprasad/f292f94657728de45d1614a741928308
#
# More help and links:
# Old version of the hack: http://bit.ly/2fsyM5X
# Blog article explaining the problem: http://bit.ly/2gnX5i1
# To make it work in Django 1.9: https://stackoverflow.com/a/29739109
#
class UnManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run.
    Many thanks to the Caktus Group: http://bit.ly/1N8TcHW
    """

    def setup_test_environment(self, *args, **kwargs):
        from django.apps import apps
        self.unmanaged_models = [m for m in apps.get_models() if not m._meta.managed]
        for m in self.unmanaged_models:
            m._meta.managed = True
        super(UnManagedModelTestRunner, self).setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super(UnManagedModelTestRunner, self).teardown_test_environment(*args, **kwargs)
        # reset unmanaged models
        for m in self.unmanaged_models:
            m._meta.managed = False

if 'test' in sys.argv or 'test_coverage' in sys.argv:  # Covers regular testing and django-coverage
    MIGRATION_MODULES = DisableMigrations()
    TEST_RUNNER = 'myresel.settings.UnManagedModelTestRunner'

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


# QOS Conf

# Number of batchs to do, smaller is faster but less precise
BANDWIDTH_BATCHS = 50


# Redis conf
RQ_QUEUES = {
   'default': {
       'HOST': REDIS_HOST,
       'PORT': REDIS_PORT,
       'DB': REDIS_DB,
   },
}
RQ_SHOW_ADMIN_LINK = True


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
            'host': 'orion.adm.resel.fr',
            'port': 5959,  # Default value: 5959
            'version': 1,
            'message_type': 'logstash',
            'fqdn': False,  # Fully qualified domain name. Default value: false.
            'tags': None,  # list of tags. Default: None.
        },
    },
    'loggers': {
        'default': {
            'handlers': ['file', 'mail_admins', 'logstash'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'mail_admins', 'logstash'],
            'level': 'DEBUG',
            'propagate': True,
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
    },
}


if DEBUG or TESTING:
    LOGGING = DEBUG_LOGGING_CONF
else:
    LOGGING = PROD_LOGGING_CONF
