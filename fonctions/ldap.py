from ldap3 import Server, Connection
from inscription.constantes import *

def search(dn, query):
    """ Fonction pour rechercher dans le ldap une entrée particulière 
        
        - dn : le DN dans lequel faire la recherche
        - query : la recherche en elle-même (uid, host, ip, mac, etc.)
    """

    res = False
    l = Connection(Server(LDAP, use_ssl = True), auto_bind = True)
    if l.search(dn, query):
        res = l.entries
    l.unbind()
    return res

def add(dn, object_class, attributes):
    """ Fonction qui ajoute une fiche au LDAP """

    l = Connection(Server(LDAP, use_ssl = True), user = DN_ADMIN, password = PASSWD_ADMIN)
    l.add(dn, object_class, attributes)
    l.unbind()