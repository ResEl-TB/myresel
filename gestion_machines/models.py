import ldapdb
import time
from ldapdb.models.fields import CharField, ListField

from fonctions.network import get_campus
from myresel import settings
from myresel.credentials import LDAP_DN_MACHINES


class LdapDevice(ldapdb.models.Model):
    """
    Represent a device in the ldap
    """

    base_dn = LDAP_DN_MACHINES
    object_classes = ['reselMachine']

    hostname = CharField(db_column='host', max_length=20, primary_key=True)
    owner = CharField(db_column='uidproprio', max_length=85)
    ip = CharField(db_column='iphostnumber', max_length=7, unique=True)
    mac_address = CharField(db_column='macaddress', max_length=20, unique=True)
    zone = ListField(db_column='zone')
    aliases = ListField(db_column='hostalias')
    last_date = CharField(db_column='lastdate', max_length=50)

    def set_owner(self, owner_uid):
        self.owner = 'uid=%s,' % str(owner_uid) + settings.LDAP_DN_PEOPLE

    def add_zone(self, z):
        self.zone.append(z)

    def get_status(self, current_campus="Brest"):
        if 'inactive' in [z.lower() for z in self.zone]:
            # Machine inactive, on renvoit le status 'inactif'
            return 'inactive'

        elif current_campus.lower() in [z.lower() for z in self.zone]:
            return 'active'

        # Computer in the wrong campus
        return 'disabled'

    def set_campus(self, campus="Brest"):
        CAMPUS = ['Brest', 'Rennes']  # TODO: move that to settings

        if campus not in CAMPUS:
            raise ValueError("Campus %s doesn't exist" % campus)

        for i in range(len(self.zone)):
            if self.zone[i] in CAMPUS:
                self.zone[i] = campus

    def activate(self, campus):
        self.zone = ['User']
        self.set_campus(campus)
        self.last_date = time.strftime('%Y%m%d%H%M%S') + 'Z'

    def add_alias(self, alias):
        self.aliases.append(alias)

    def remove_alias(self, alias):
        self.aliases.remove(alias)
