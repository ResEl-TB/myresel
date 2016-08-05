"""
Credentials for the ResEl website
"""

# LDAP

LDAP_URL = "ldap.resel.fr"
LDAP_PORT = "389"
LDAP_PASSWD = 'blah'

LDAP_DC = "dc=maisel,dc=enst-bretagne,dc=fr"
LDAP_DN_PEOPLE = 'ou=people,%s' % LDAP_DC
LDAP_DN_MACHINES = 'ou=machines,%s' % LDAP_DC
LDAP_DN_ADMIN = 'cn=admin,%s' % LDAP_DC


# ADMIN DATABASE

DB_ADMIN_HOST = "maia.adm.resel.fr"
DB_ADMIN_USER = "myresel"
DB_ADMIN_PASSWORD = "blah"


# REDIS

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0