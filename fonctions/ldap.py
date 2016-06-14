from ldap3 import Server, Connection, MODIFY_REPLACE
from myresel.constantes import *
from .network import *
from .generic import get_year

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

    l = Connection(Server(LDAP, use_ssl = True), user = DN_ADMIN, password = PASSWD_ADMIN).bind()
    l.add(dn, object_class, attributes)
    l.unbind()
    network.update_all()

def get_status(ip):
    """ Fonction pour trouver le status d'une machine :
        - active
        - inactive
        - mauvais campus
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

def update_campus(ip):
    """ Modifie le LDAP pour attribuer le bon campus à la machine qui possède l'ip fournie """

    CAMPUS = ['Brest', 'Rennes']

    mac = get_mac(ip)
    campus = get_campus(ip)
    machine = search(DN_MACHINES, '(&(macaddress=%s))' % mac, ['zone', 'host'])[0]

    # Récupération de l'ancien campus de la machine
    for z in machine.zone:
        if z.capitalize() in CAMPUS:
            old_campus = z.capitalize()

    # Update de la fiche LDAP
    l = Connection(Server(LDAP, use_ssl = True), user = DN_ADMIN, password = PASSWD_ADMIN).bind()
    l.modify('host=%s,' % machine.host[0] + DN_MACHINES,
             {'zone': [(MODIFY_REPLACE, ['User', campus])]})
    l.unbind()
    update_all()

def reactivation(ip):
    """ Modifie le LDAP pour réactiver la machine de l'utilisateur """

    mac = get_mac(ip)
    campus = get_campus(ip)
    machine = search(DN_MACHINES, '(&(macaddress=%s))' % mac, ['host'])[0]

    l = Connection(Server(LDAP, use_ssl = True), user = DN_ADMIN, password = PASSWD_ADMIN).bind()
    l.modify('host=%s,' % machine.host[0] + DN_MACHINES,
             {'zone': [(MODIFY_REPLACE, ['User', campus])]})
    l.unbind()
    update_all()

def get_free_ip(low, high):
    """ Récupère une IP libre pour une nouvelle machine à partir du LDAP """

    rang = low - 1
    again = True

    while ((rang < high) and again):
        rang += 1
        item = 2

        while ((item < 254) and again):
            item +=1
            if not search(DN_MACHINES, '(&(ipHostNumber={}.{}))'.format(rang, item)):
                again = False

    return "{}.{}".format(rang, item)

def get_free_alias(uid):
    """ Récupère un nom d'alias libre pour la machine """

    again = True
    alias = 'pc' + uid
    i = 1

    while again:
        if not search(DN_MACHINES, '(|(host=%(alias)s)(hostalias=%(alias)s))' % {'alias': alias}):
            again = False
        else:
            i += 1
            alias = 'pc' + uid + str(i)

    return alias

def cotisation(user, duree):
    """ On stocke dans le LDAP la date de fin de cotisation """

    l = Connection(Server(LDAP, use_ssl = True), user = DN_ADMIN, password = PASSWD_ADMIN)
    l.modify(
        'uid=%s,' % user + DN_PEOPLE,
        {'cotiz': [(MODIFY_REPLACE, [str(generic.get_year())])],
         'endInternet': [(MODIFY_REPLACE, [generic.get_end_date(duree)])]}
    )
    l.unbind()
    update_all()