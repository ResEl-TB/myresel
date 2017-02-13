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

    def is_member(self, uid):
        return uid in [member.split(',')[0].split('uid=')[1] for member in self.members]

from campus.models.rooms_models import *
from campus.models.mails_models import *
from campus.models.clubs_models import *