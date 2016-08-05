# coding=utf-8
#
# Summarise specifics settings for an installation
# Usually here is what differ from production and development configuration
#

SECRET_KEY = '7_gz^zjk+lj+72utudq+l(xd-!@3xlo5c*20&dz$mdgn2p22g-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SSL configuration

# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

# SESSION_COOKIE_SECURE = False

# CSRF_COOKIE_SECURE = False

# SESSION_EXPIRE_AT_BROWSER_CLOSE = False

#####
# Credentials, please keep them out of the repo
#####

# LDAP CREDENTIALS

LDAP_URL = "localhost"
LDAP_PORT = "389"
LDAP_PASSWD = 'blah'

LDAP_DC_MAISEL = "dc=maisel,dc=enst-bretagne,dc=fr"
LDAP_DC_RESEL = "dc=resel,dc=enst-bretagne,dc=fr"
LDAP_DN_PEOPLE = 'ou=people,%s' % LDAP_DC_MAISEL
LDAP_DN_MACHINES = 'ou=machines,%s' % LDAP_DC_RESEL
LDAP_DN_ADMIN = 'cn=admin,%s' % LDAP_DC_MAISEL

LDAP_ECOLE = "0.0.0.0"
LDAP_ECOLE_DN = ""


# DATABASE CREDENTIALS

DB_NAME = "resel"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "blah"


# REDIS CREDENTIALS

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0


# STRIPE CREDENTIALS

STRIPE_API_KEY = "sk_test_Uk3Qcg8o0OTj8VHAG6NovqR9"