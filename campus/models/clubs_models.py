# -*- coding: utf-8 -*-

import ldapback
from ldapback.models.fields import LdapCharField, LdapListField, LdapCharField, LdapBooleanField
from myresel.settings import LDAP_OU_CLUBS

class StudentOrganisation(ldapback.models.LdapModel):
    """
    The class having all the element for a club
    """
    base_dn = LDAP_OU_CLUBS
    object_classes = LdapListField(db_column='objectClass')

    # studentOrganisation
    cn = LdapCharField(db_column='cn', object_classes=['studentOrganisation'], pk=True)
    name = LdapCharField(db_column='orgaName', object_classes=['studentOrganisation'])
    prezs = LdapListField(db_column='uidPrezs', object_classes=['studentOrganisation','tbClub'])
    members = LdapListField(db_column='uidMembres', object_classes=['studentOrganisation','tbClub'])
    ml_infos = LdapBooleanField(db_column='mlInfos', object_classes=['studentOrganisation'])
    email = LdapCharField(db_column='mlist', object_classes=['studentOrganisation'])
    website = LdapCharField(db_column='website', object_classes=['studentOrganisation'])
    description = LdapCharField(db_column='description', object_classes=['studentOrganisation'])
    logo = LdapCharField(db_column='logo', object_classes=['studentOrganisation'])

    #tbCampagne
    campagneYear = LdapCharField(db_column='campagneYear', object_classes=['tbCampagne'])

    def __str__(self):
        return self.name
