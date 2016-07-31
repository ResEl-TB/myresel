import itertools
from ldap3 import Server, Connection, MODIFY_REPLACE
from .network import get_campus, get_mac, update_all
from .generic import current_year
from django.conf import settings
from fonctions import generic
from datetime import datetime

def new_connection():
    """
    Return a new connection to the database, must be unbind after all
    :return:
    """
    return Connection(
        Server(settings.LDAP_URL, use_ssl=True),
        user=settings.LDAP_DN_ADMIN,
        password=settings.LDAP_PASSWD,
        auto_bind=True
    )


def search(dn, query, attr=None):
    """ Fonction pour rechercher dans le ldap une entrée particulière 
        
        - dn : le DN dans lequel faire la recherche
        - query : la recherche en elle-même (uid, host, ip, mac, etc.)
        - attr : les attributs à extraire de la fiche LDAP
    """

    res = False
    l = new_connection()
    if l.search(dn, query, attributes=attr):
        res = l.entries
    l.unbind()
    return res


def add(dn, object_class, attributes):
    """ Fonction qui ajoute une fiche au LDAP """

    l = new_connection()
    l.add(dn, object_class, attributes)
    l.unbind()
    update_all()


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

    res = search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % mac, ['zone'])
    if res:
        if 'inactive' in [z.lower() for z in res[0].zone]:
            # Machine inactive, on renvoit le status 'inactif'
            return 'inactive'

        elif campus.lower() not in [z.lower() for z in res[0].zone]:
            # Machine sur le mauvais campus
            return 'wrong_campus'

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
    machine = search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % mac, ['zone', 'host'])[0]

    # Récupération de l'ancien campus de la machine
    for z in machine.zone:
        if z.capitalize() in CAMPUS:
            old_campus = z.capitalize()

    # Update de la fiche LDAP
    l = new_connection()
    l.modify('host=%s,' % machine.host[0] + settings.LDAP_DN_MACHINES,
             {'zone': [(MODIFY_REPLACE, ['User', campus])]})
    l.unbind()
    update_all()


def reactivation(ip):
    """ Modifie le LDAP pour réactiver la machine de l'utilisateur """

    mac = get_mac(ip)
    campus = get_campus(ip)
    machine = search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % mac, ['host'])[0]
    dn = 'host=%s,' % machine.host[0] + settings.LDAP_DN_MACHINES
    modifs = {'zone': [(MODIFY_REPLACE, ['User', campus])]}
    modify(dn, modifs)
    update_all()


def modify(dn, modifs):
    """ Modifie une fiche LDAP """

    l = new_connection()
    l.modify(dn, modifs)
    l.unbind()


def get_free_ip(low, high):
    """ Retreive a free ip from the ldap """

    return next(
        "%i.%i" % ip
        for ip in itertools.product(range(low - 1, high), range(2, 254))
        if not search(settings.LDAP_DN_MACHINES, '(&(ipHostNumber=%i.%i))' % ip)
    )


def get_free_alias(uid):
    """ Récupère un nom d'alias libre pour la machine """

    again = True
    alias = 'pc' + uid
    i = 1

    while again:
        if not search(settings.LDAP_DN_MACHINES, '(|(host=%(alias)s)(hostalias=%(alias)s))' % {'alias': alias}):
            again = False
        else:
            i += 1
            alias = 'pc' + uid + str(i)

    return alias


def cotisation(user, duree):
    """ On stocke dans le LDAP la date de fin de cotisation """

    l = new_connection()
    l.modify(
        'uid=%s,' % user + settings.LDAP_DN_PEOPLE,
        {'cotiz': [(MODIFY_REPLACE, [str(generic.current_year())])],
         'endCotiz': [(MODIFY_REPLACE, [generic.get_end_date(duree)])]}
    )
    l.unbind()
    update_all()

def need_to_pay(username):
    """ Check is the user needs to pay his fee or not """

    user = search(settings.LDAP_DN_PEOPLE, '(&(uid=%s))' % username, ['cotiz', 'endcotiz'])[0]
    if 'cotiz' in user.entry_to_json().lower() and 'endcotiz' in user.entry_to_json().lower():
        end_date = datetime.strptime(user.endcotiz[0], '%Y%m%d%H%M%SZ')
        if end_date < datetime.now():
            return True
        else:
            return False
    else:
        return True
