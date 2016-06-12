from ldap3 import Server, Connection
from myresel.constantes import *
from .network import *

def search(dn, query, attr = None):
    """ Fonction pour rechercher dans le ldap une entrée particulière 
        
        - dn : le DN dans lequel faire la recherche
        - query : la recherche en elle-même (uid, host, ip, mac, etc.)
        - attr : les attributs à extraire de la fiche LDAP
    """

    res = False
    l = Connection(Server(LDAP, use_ssl = True), auto_bind = True)
    if l.search(dn, query, attributes = attr):
        res = l.entries
    l.unbind()
    return res

def add(dn, object_class, attributes):
    """ Fonction qui ajoute une fiche au LDAP """

    l = Connection(Server(LDAP, use_ssl = True), user = DN_ADMIN, password = PASSWD_ADMIN)
    l.add(dn, object_class, attributes)
    l.unbind()

def get_status(ip):
    """ Fonction pour trouver le status d'une machine :
        - active
        - inactive
        - inexistante
    """

    # Identification du campus
    campus = get_campus(ip)

    # Récupération de l'adresse mac associée à l'IP
    mac = get_mac(ip)

    res = search(DN_MACHINES, '(&(macaddress=%s))' % mac, ['zone'])
    if res:
        if 'inactive' in [z.lower() for z in res[0].zone]:
            # Machine inactive, on renvoit le status 'inactif'
            return 'inactive'

        elif campus.lower() not in [z.lower() for z in res[0].zone]:
            # Machine sur le mauvais campus
            return 'mauvais_campus'

        else:
            # Machine présente dans le LDAP, marquée comme active
            return 'active'

    # Machine inexistante dans le LDAP
    return False