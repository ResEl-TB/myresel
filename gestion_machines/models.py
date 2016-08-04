import ldapdb
import time
from ldapdb.models.fields import CharField, ListField

from myresel import settings
from myresel.credentials import LDAP_DN_MACHINES


class LdapDevice(ldapdb.models.Model):
    """
    Represent a device in the ldap
    """

    CAMPUS = ['Brest', 'Rennes']  # TODO: move that to settings

    base_dn = LDAP_DN_MACHINES
    object_classes = ['reselMachine']

    hostname = CharField(db_column='host', max_length=20, primary_key=True)
    owner = CharField(db_column='uidproprio', max_length=85)
    ip = CharField(db_column='iphostnumber', max_length=7, unique=True)
    mac_address = CharField(db_column='macaddress', max_length=20, unique=True)
    zones = ListField(db_column='zone')
    aliases = ListField(db_column='hostalias')
    last_date = CharField(db_column='lastdate', max_length=50)

    def set_owner(self, owner_uid):
        self.owner = 'uid=%s,' % str(owner_uid) + settings.LDAP_DN_PEOPLE

    def add_zone(self, z):
        self.zones.append(z)

    def get_status(self):
        """
        Return the machine status :
        inactive : the device wasn't seen in a long time
        active : the device is ready and working
        wrong campus : the device is on the wrong campus
        :return:
        """
        current_campus = self.get_campus()
        if 'inactive' in [z.lower() for z in self.zones]:
            return 'inactive'

        elif current_campus.lower() in [z.lower() for z in self.zones]:
            return 'active'

        # Computer in the wrong campus
        return 'wrong_campus'

    def set_campus(self, campus="Brest"):
        if campus not in self.CAMPUS:
            raise ValueError("Campus %s doesn't exist" % campus)

        for i in range(len(self.zones)):
            if self.zones[i] in self.CAMPUS:
                self.zones[i] = campus

    def get_campus(self):
        for zone in self.zones:
            if zone in self.CAMPUS:
                return zone
        return None

    def activate(self, campus):
        """
        Activate a device on the chosen campus
        Doesn't look why the device was deactivated
        :param campus:
        :return:
        """
        self.zones = ['User']
        self.set_campus(campus)
        self.last_date = time.strftime('%Y%m%d%H%M%S') + 'Z'

    def add_alias(self, alias):
        self.aliases.append(alias)

    def remove_alias(self, alias):
        self.aliases.remove(alias)
