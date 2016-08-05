"""
Credentials for the ResEl website
"""

# LDAP

LDAP_URL = "localhost"
LDAP_PORT = "389"
LDAP_PASSWD = 'blah'

LDAP_DC = "dc=maisel,dc=enst-bretagne,dc=fr"
LDAP_DN_PEOPLE = 'ou=people,%s' % LDAP_DC
LDAP_DN_MACHINES = 'ou=machines,%s' % LDAP_DC
LDAP_DN_ADMIN = 'cn=admin,%s' % LDAP_DC
LDAP_ADMIN = 'cn=admin,%s' % LDAP_DC

LDAP_ECOLE = "10.29.90.34"
LDAP_ECOLE_DN = "ou=people,o=unix,dc=enst-bretagne,dc=fr"


# DATABASE

DB_NAME = "resel"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "blah"


# REDIS

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0


# STRIPE

STRIPE_API_KEY = "sk_test_Uk3Qcg8o0OTj8VHAG6NovqR9"