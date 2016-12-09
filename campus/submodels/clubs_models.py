import ldapback
from ldapback.models.fields import LdapCharField, LdapListField, LdapCharField
from myresel.settings import LDAP_OU_CLUBS

class Club(ldapback.models.LdapModel):
    """
    The class having all the element for a user
    """
    base_dn = LDAP_OU_CLUBS
    object_classes = ['tbClub']

    # tbClub
    name = LdapCharField(db_column='orgaName', object_classes=['tbClub'], pk=True)
    prezs = LdapListField(db_column='uidPrezs', object_classes=['tbClub'])
    members = LdapListField(db_column='uidMembres', object_classes=['tbClub'])