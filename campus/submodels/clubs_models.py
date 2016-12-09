import ldapback
from ldapback.models.fields import LdapCharField, LdapListField, LdapCharField, LdapBooleanField
from myresel.settings import LDAP_OU_CLUBS

class Club(ldapback.models.LdapModel):
    """
    The class having all the element for a user
    """
    base_dn = LDAP_OU_CLUBS
    object_classes = ['tbClub']

    # tbClub
    cn = LdapCharField(db_column='cn', object_classes=['tbClub'], pk=True)
    name = LdapCharField(db_column='orgaName', object_classes=['tbClub'])
    prezs = LdapListField(db_column='uidPrezs', object_classes=['tbClub'])
    members = LdapListField(db_column='uidMembres', object_classes=['tbClub'])
    ml_infos = LdapBooleanField(db_column='mlInfos', object_classes=['tbClub'])

    def __str__(self):
        return self.name