"""
Django settings for myresel project.

Generated by 'django-admin startproject' using Django 1.9.6.
"""

import os

from django.utils.translation import ugettext_lazy as _

from myresel.credentials import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6_gz^zjk+lj+72utudq+l(xd-!@3xlo5c*20&dz$mdgn2p22g-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['my.resel.fr', 'resel.fr']

# Mails

SERVER_EMAIL = 'inscription@resel.fr'

EMAIL_USE_TLS = True

EMAIL_HOST = 'pegase.adm.resel.fr'

EMAIL_SUBJECT_PREFIX = ''

# Login

LOGIN_URL = '/login'

LOGIN_REDIRECT_URL = '/'

# Inscription zone 

INSCRIPTION_ZONE_FALLBACK_URL = '/inscription_zone/'

INSCRIPTION_ZONE_ALLOWED_URLS = [
                                r'^$',
                                r'^login',
                                r'^machines/'
                                r'^personnes/',
                                r'^paiement/',
                                r'^contact/',
                                ]

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
    'modeltranslation', #Must be before contrib.admin 
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
    'myresel.middleware.IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAReselAdminSoCheckTheLdapBeforeMiddleaware',
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
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': 'ldap://%s:%s' % (LDAP_URL, LDAP_PORT),
        'USER': LDAP_DN_ADMIN,
        'PASSWORD': LDAP_PASSWD,
     },
}
DATABASE_ROUTERS = ['ldapdb.router.Router']

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
