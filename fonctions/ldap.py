import itertools
from datetime import datetime, timedelta

from django.conf import settings
from django_python3_ldap.ldap import Connection as UserConnection
from ldap3 import Server, Connection, MODIFY_REPLACE, ALL_ATTRIBUTES

from fonctions import generic
from .generic import hash_passwd
from .network import get_campus, get_mac, update_all


def new_connection():
    """
    Return a new connection to the database, must be unbind after all
    :return:
    """
    return Connection(
        Server(settings.LDAP_URL, use_ssl=False),
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


def get_user(**kwargs):
    l = new_connection()
    c = UserConnection(l)
    return c.get_user(**kwargs)


def search_ecole(query):
    """ Fonction pour rechercher dans le ldap école une entrée particulière

        query : la recherche
    """

    res = False
    l = Connection(
        Server(settings.LDAP_ECOLE, use_ssl=True),
        auto_bind=True
    )
    if l.search(settings.LDAP_ECOLE_DN, query, attributes=ALL_ATTRIBUTES):
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
    # TODO: viruses computers
    # Identification du campus
    campus = get_campus(ip)

    # Récupération de l'adresse mac associée à l'IP
    mac = get_mac(ip)

    res = search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % mac, ['zone'])
    if res:
        if 'inactive' in [z.lower() for z in res[0].zone]:
            # Machine inactive, on renvoit le status 'inactif'
            return 'inactive'

        elif campus.lower() in [z.lower() for z in res[0].zone]:
            return 'active'

        else:
            # Computer in the wrong campus
            return 'disabled'

    # Computer not in the ldap
    return 'unknown'


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
        for ip in itertools.product(range(low, high+1), range(1, 255))
        if not search(settings.LDAP_DN_MACHINES, '(&(ipHostNumber=%i.%i))' % ip)
    )


def get_free_alias(name, prefix='pc'):
    """
    Get a free alias from the ldap in the form
    prefix + name + nbr
    :param name: name of the computer (for example the user uid)
    :param prefix: machine prefix
    :return:
    """

    again = True
    base_alias = prefix + name
    alias = base_alias
    i = 1

    while again:
        if not search(settings.LDAP_DN_MACHINES, '(|(host=%(alias)s)(hostalias=%(alias)s))' % {'alias': alias}):
            again = False
        else:
            i += 1
            alias = base_alias + str(i)

    return alias


def cotisation(user, duree):
    """ On stocke dans le LDAP la date de fin de cotisation """

    l = new_connection()
    l.modify(
        'uid=%s,' % user + settings.LDAP_DN_PEOPLE,
        {'cotiz': [(MODIFY_REPLACE, [str(generic.current_year())])],
         'endInternet': [(MODIFY_REPLACE, [generic.get_end_date(duree)])]}
    )
    l.unbind()
    update_all()

def need_to_pay(username):
    """ Check is the user needs to pay his fee or not """

    user = search(settings.LDAP_DN_PEOPLE, '(&(uid=%s))' % username, ['cotiz', 'endinternet'])
    if user:
        user = user[0]
        if 'cotiz' in user.entry_to_json().lower() and 'endinternet' in user.entry_to_json().lower():
            end_date = datetime.strptime(user.endinternet[0], '%Y%m%d%H%M%SZ')
            if end_date < datetime.now():
                return 'danger'
            elif end_date < (datetime.now() + timedelta(days=7)):
                return 'warning'
            else:
                return 'success'
        else:
            return 'danger'


def create_admin():
    l = new_connection()
    dn = "uid=lcarr,ou=admins,dc=resel,dc=enst-bretagne,dc=fr"
    object_class = "reselAdmin"
    attributes = {
        'uid': 'lcarr',
        'userpassword': hash_passwd("123zizou"),
        'droit': ["Cisco",
                  "ae",
                  "agora",
                  "annuaire",
                  "backuppc",
                  "cotiz",
                  "documentation",
                  "ldapadmin",
                  "photo",
                  "reseladmin",
                  "svn",
                  "trac",
                  "tracadmin"]
    }
    # l.delete(dn)
    l.add(dn, object_class, attributes)
    l.unbind()
