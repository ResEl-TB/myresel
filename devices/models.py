# -*- coding: utf-8 -*-
import logging
import requests
import time

import ldapback
from ldapback.models.fields import LdapCharField, LdapListField, LdapDatetimeField
from myresel import settings
from myresel.settings import LDAP_DN_MACHINES

logger = logging.getLogger("default")


class LdapDevice(ldapback.models.LdapModel):
    """
    Represent a device in the ldap
    """

    base_dn = LDAP_DN_MACHINES
    object_classes = LdapListField(db_column='objectClass')

    owner = LdapCharField(db_column='uidproprio', object_classes=['reselDevice'], required=True)
    mac_address = LdapCharField(db_column='macAddress', object_classes=['reselDevice'], required=True, pk=True)
    auth_type = LdapCharField(db_column='authType', object_classes=['reselDevice'], required=True)
    last_date = LdapDatetimeField(db_column='lastDate', object_classes=['reselDevice'])
    host = LdapCharField(db_column='host', object_classes=['reselDevice'])

    def pretty_mac(self):
        s = self.mac_address.upper()
        return ':'.join(a+b for a,b in zip(s[::2], s[1::2]))

    def set_owner(self, owner_uid):
        self.owner = 'uid=%s,' % str(owner_uid) + settings.LDAP_DN_PEOPLE

    def default_host(self):
        for ip in settings.DHCP_API:
            try:
                resp = requests.get(url='http://%s/v0/leases?state=active&mac=%s' % (ip, self.mac_address))
                leases = resp.json()
            except requests.exceptions.RequestException:
                logger.warning("L'API %s ne répond pas" % ip, extra={"ip": ip})
                continue
            except ValueError:
                logger.warning("L'appel à l'API %s a retourné un contenu incorrect" % ip,
                               extra={"ip": ip})
                continue
            if leases and 'client-hostname' in leases[-1]:
                return leases[-1]['client-hostname']
        return None

    def get_host(self):
        if self.host:
            return self.host
        return self.default_host()
