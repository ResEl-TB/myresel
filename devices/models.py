# -*- coding: utf-8 -*-
import time

import ldapback
from ldapback.models.fields import LdapCharField, LdapListField
from myresel import settings
from myresel.settings import LDAP_DN_MACHINES


class LdapDevice(ldapback.models.LdapModel):
    """
    Represent a device in the ldap
    """

    base_dn = LDAP_DN_MACHINES
    object_classes = LdapListField(db_column='objectClass')

    owner = LdapCharField(db_column='uidproprio', object_classes=['reselDevice'], required=True)
    mac_address = LdapCharField(db_column='macAddress', object_classes=['reselDevice'], required=True, pk=True)
    auth_type = LdapCharField(db_column='authType', object_classes=['reselDevice'], required=True)
    last_date = LdapCharField(db_column='lastdate', object_classes=['reselDevice'])

    def pretty_mac(self):
        s = self.mac_address.upper()
        return ':'.join(a+b for a,b in zip(s[::2], s[1::2]))

    def set_owner(self, owner_uid):
        self.owner = 'uid=%s,' % str(owner_uid) + settings.LDAP_DN_PEOPLE
