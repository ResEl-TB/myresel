from campus.submodels.rooms_models import *
from campus.submodels.mails_models import *
from campus.submodels.clubs_models import *

import ldapback
from ldapback.models.fields import LdapCharField, LdapListField
from myresel.settings import LDAP_DN_GROUPS

class LdapGroup(ldapback.models.LdapModel):
    """
    The class managing the groups in the LDAP
    """

    base_dn = LDAP_DN_GROUPS
    object_classes = ['groupOfNames']

    cn = LdapCharField(db_column='cn', object_classes=['groupOfNames'], pk=True)
    members = LdapListField(db_column='member', object_classes=['groupOfNames'])