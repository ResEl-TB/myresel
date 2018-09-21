import itertools
import logging

from django.conf import settings
from django.template.defaultfilters import slugify
from django_python3_ldap.ldap import Connection as UserConnection
from ldap3 import Server, Connection, MODIFY_REPLACE, ALL_ATTRIBUTES

from fonctions import generic
from .generic import hash_passwd
from .network import get_campus, get_mac, update_all

logger = logging.getLogger("default")

def new_connection():
    """
    Return a new connection to the database, must be unbind after all
    :return:
    """
    return Connection(
        Server(settings.LDAP_URL, use_ssl=False),
        user=settings.LDAP_DN_ADMIN,
        password=settings.LDAP_PASSWD,
        auto_bind=settings.LDAP_AUTO_BIND
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

    attr = ('uid', 'sn', 'displayName', 'mail','title', 'givenName', 'l')
    if l.search(settings.LDAP_ECOLE_DN, query, attributes=attr):
        data = []
        for entry in l.entries:
            data.append(entry.entry_to_json())
        res = data
    l.unbind()
    return res

def get_status(ip):
    """ Fonction pour trouver le status d'une machine :
        - active
        - inactive
        - mauvais campus
        - inexistante

    Cette fonction va d'abord rechercher la mac associée à l'ip, puis faire
    la recherche ldap associée. Cela permet une plus grande réactivitée,
    en particulier quand le bail DHCP n'est pas à jour.
    :param: ip adresse de la machine à vérifier
    :return: string
    """
    # TODO: viruses computers
    # Identification du campus
    campus = get_campus(ip)

    # Récupération de l'adresse mac associée à l'IP
    mac = get_mac(ip)  # TODO: use something else than re-requesting the network, which is slow

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


def ip_in_ldap(ip_suff):
    """Check if an ip suffix is in the ldap"""
    return search(settings.LDAP_DN_MACHINES, '(&(ipHostNumber=%s))' % ip_suff)


def get_free_ip(low, high):
    """ Retreive a free ip from the ldap """
    import redis
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
        )
        while True:
            ip_suff = r.spop(settings.REDIS_AV_IPS_KEY)
            if ip_suff is None:
                logger.warning(
                    'No ip available in redis ips buffer, consider increase the buffer size',
                    extra={'message_code': 'REDIS_IP_BUFFER_EMPTY'}
                )
                break
            ip_suff = ip_suff.decode('utf-8')
            if not ip_in_ldap(ip_suff):
                logger.info(
                    'IP %s used as free ip' % ip_suff,
                    extra={'ip_address': ip_suff, 'message_code': 'CHOOSED_IP'}
                )
                return ip_suff

    except redis.exceptions.ConnectionError as e:
        logger.error(
            'Redis Server Unavailable : %s' % str(e),
            extra={'message_code': 'REDIS_CONNECTION_ERROR'},
        )

    logger.info(
        'Fallback to default ip fetching',
        extra={'message_code': 'DEFAULT_IP_FETCHING_FALLBACK'},
    )
    choosed_ip = next(
        "%i.%i" % ip
        for ip in itertools.product(range(low, high+1), range(1, 255))
        if not search(settings.LDAP_DN_MACHINES, '(&(ipHostNumber=%i.%i))' % ip)
    )

    logger.info(
        'IP %s used as free ip' % choosed_ip,
        extra={'ip_address': choosed_ip, 'message_code': 'CHOOSED_IP'}
    )
    return choosed_ip

def get_free_alias(name, prefix='pc'):
    """
    Get a free alias from the ldap in the form
    prefix + name + nbr
    :param name: name of the computer (for example the user uid)
    :param prefix: machine prefix
    :return:
    """

    # Name was assumed to be safe, but on the 2016-10-03 we discovered
    # That some users have bad formed uid. So I now I suppose nothing is
    # safe here...
    name = slugify(name)

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

    logger.info(
        'Alias %s used as free alias' % alias,
        extra={'alias': alias, 'message_code': 'CHOOSED_ALIAS'}
    )
    return alias


def create_admin(uid='lcarr', pwd="blahblah"):
    """
    Create a new administrator, should be used for tests only
    :param uid:
    :param pwd:
    :return:
    """
    if not settings.DEBUG and not settings.TESTING:
        raise Exception("MUST NOT BE CALLED IN PRODUCTION")

    l = new_connection()
    dn = "uid=lcarr,ou=admins,dc=resel,dc=enst-bretagne,dc=fr"
    object_class = "reselAdmin"
    attributes = {
        'uid': uid,
        'userpassword': hash_passwd(pwd),
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
    try:
        l.delete(dn)
    except:
        pass
    l.add(dn, object_class, attributes)
    l.unbind()
    return dn
