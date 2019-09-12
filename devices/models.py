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
    object_classes = ['reselDevice']

    owner = LdapCharField(db_column='uidproprio', object_classes=object_classes, required=True)
    mac_address = LdapCharField(db_column='macAddress', object_classes=object_classes, required=True)
    auth_type = LdapCharField(db_column='authType', object_classes=object_classes, required=True)
    last_date = LdapCharField(db_column='lastdate', object_classes=object_classes)

    def pretty_mac(self):
        s = self.mac_address.upper()
        return ':'.join(a+b for a,b in zip(s[::2], s[1::2]))

    def set_owner(self, owner_uid):
        self.owner = 'uid=%s,' % str(owner_uid) + settings.LDAP_DN_PEOPLE
