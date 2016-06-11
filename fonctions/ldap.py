from ldap3 import Server, Connection
from inscription.constantes import *

def search(dn, query):
    """ Fonction pour rechercher dans le ldap une entrée particulière 
        
        - dn : le DN dans lequel faire la recherche
        - query : la recherche en elle-même (uid, host, ip, mac, etc.)
    """

    l = Connection(Server(LDAP, use_ssl = True), auto_bind = True)

    # On effectue la recherche des machines actives sur Brest
    l.search(dn, query)
    res = l.entries
    l.unbind()

    # On retourne les résultats
    return res

def search_ecole(uid):
    """ Cherche dans le LDAP école des infos sur les user """

    l = Connection(Server(LDAP_ECOLE), auto_bind = True)
    l.search(DN_ECOLE, '(&(uid=%s))' % uid, attributes = ['cn', 'mail'])
    res = l.entries
    l.unbind()
    return res
