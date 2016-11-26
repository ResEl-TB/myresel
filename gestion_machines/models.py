import time

from django.db import models
from django.db.models import CharField, IntegerField, BigIntegerField

import ldapback
from ldapback.models.fields import LdapCharField, LdapListField
from myresel import settings
from myresel.settings import LDAP_DN_MACHINES


class PeopleData(models.Model):

    UP = 'up'
    DOWN = 'down'
    WAY_CHOICES = (
        (UP, 'up'),
        (DOWN, 'down'),
    )

    CLEAN = 'clean'
    DIRTY = 'dirty'
    FLOW_CHOICES = (
        (CLEAN, 'clean'),
        (DIRTY, 'dirty')
    )

    site = CharField(max_length=32, default=None, db_column="site", editable=False)
    cn = CharField(max_length=128, default=None, db_column="cn", editable=False, primary_key=True)
    uid = CharField(max_length=16, default=None, db_column="uid", editable=False)
    way = CharField(max_length=4, default=None, db_column="way", editable=False, choices=WAY_CHOICES)
    flow = CharField(max_length=5, default=None, db_column="flow", editable=False, choices=FLOW_CHOICES)

    group = IntegerField(default=None, db_column="group", editable=False)
    amount = BigIntegerField(default=None, db_column="amount", editable=False)
    amount_ponderated = BigIntegerField(default=None, db_column="amount_ponderated", editable=False)
    last_rate = IntegerField(default=None, db_column="last_rate", editable=False)

    class Meta:
        db_table = "people_data"
        managed = False
        default_permissions = ()
        index_together = [
            ["cn", "way", "flow", "site"],
        ]


class PeopleHistory(models.Model):
    class Meta:
        db_table = "people_history"
        managed = False
        default_permissions = ()


class LdapDevice(ldapback.models.LdapModel):
    """
    Represent a device in the ldap
    """
    CAMPUS = ['Brest', 'Rennes']  # TODO: move that to settings

    base_dn = LDAP_DN_MACHINES
    object_classes = ['reselMachine']

    hostname = LdapCharField(db_column='host', object_classes=['reselMachine'], pk=True)
    owner = LdapCharField(db_column='uidproprio', object_classes=['reselMachine'], required=True)
    ip = LdapCharField(db_column='iphostnumber', object_classes=['reselMachine'], required=True)
    mac_address = LdapCharField(db_column='macaddress', object_classes=['reselMachine'], required=True)
    zones = LdapListField(db_column='zone', object_classes=['reselMachine'])
    aliases = LdapListField(db_column='hostalias', object_classes=['reselMachine'])
    last_date = LdapCharField(db_column='lastdate', object_classes=['reselMachine'])

    def set_owner(self, owner_uid):
        # TODO: move that to an object, an maybe check existance
        self.owner = 'uid=%s,' % str(owner_uid) + settings.LDAP_DN_PEOPLE

    def add_zone(self, z):
        if isinstance(self.zones, LdapListField):
            self.zones = [z]
        elif z not in self.zones:
            self.zones.append(z)

    def replace_or_add_zone(self, old, new):
        if isinstance(self.zones, LdapListField):
            self.zones = []
        elif old in self.zones:
            self.zones.remove(old)
        self.add_zone(new)

    def get_status(self):
        """
        Return the machine status :
        inactive : the device wasn't seen in a long time
        active : the device is ready and working
        wrong campus : the device is on the wrong campus
        :return:
        """
        current_campus = settings.CURRENT_CAMPUS
        lower_zone = [z.lower() for z in self.zones]

        if 'inactive' in lower_zone:
            return 'inactive'

        elif current_campus.lower() in lower_zone and \
                "user" in lower_zone:
            return 'active'

        # Computer in the wrong campus or in error (in some rare cases)
        return 'wrong_campus'

    def set_campus(self, campus="Brest"):
        """
        Set the campus of the computer
        :param campus:
        :return:
        """
        if campus not in self.CAMPUS:
            raise ValueError("Campus %s doesn't exist" % campus)

        old_camp = next(c for c in self.CAMPUS if c != campus)
        self.replace_or_add_zone(old_camp, campus)

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
        self.set_campus(campus)
        self.replace_or_add_zone('Inactive', 'User')
        self.last_date = time.strftime('%Y%m%d%H%M%S') + 'Z'

    def add_alias(self, alias):
        if isinstance(self.aliases, LdapListField):
            self.aliases = [alias]
        else:
            self.aliases.append(alias)

    def remove_alias(self, alias):
        """
        Remove the alias
        Raises ValueError if the alias doesn't exist
        :param alias:
        :return:
        """
        if isinstance(self.aliases, LdapListField):
            self.aliases = []
        else:
            self.aliases.remove(alias)

    def is_inactive(self):
        """
        Return True if the device is inactive in the ldap
        :return:
        """
        for zone in self.zones:
            if zone.lower() == "inactive":
                return True
        return False

class QoSRouter(object):
    """
    A router for reading in QoS database
    """
    QoSClasses = (
        PeopleData,
        PeopleHistory,
    )

    def is_qos(self, obj):
        for c in self.QoSClasses:
            if isinstance(obj(), c):
                return True
        return False

    def db_for_read(self, model, **hints):
        if self.is_qos(model):
            return 'qos'
        return None

    def db_for_write(self, model, **hints):
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if self.is_qos(obj1) or self.is_qos(obj2):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None
