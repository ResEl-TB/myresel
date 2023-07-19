# -*- coding: utf-8 -*-

import ldapback
from ldapback.models.fields import LdapListField, LdapCharField, LdapBooleanField
from myresel.settings import LDAP_OU_CLUBS


#If we don't do this we get an error cuz our LDAP scheme does not allow
# a single model for each type of organisation
class StudentOrganisation(ldapback.models.LdapModel):
    """
    The class having all the element for a club
    """

    base_dn = LDAP_OU_CLUBS

    cn = LdapCharField(db_column='cn', object_classes=['studentOrganisation'], pk=True)
    name = LdapCharField(db_column='orgaName', object_classes=['studentOrganisation', 'tbClub'])
    prezs = LdapListField(db_column='uidPrezs', object_classes=['studentOrganisation','tbClub'])
    members = LdapListField(db_column='uidMembres', object_classes=['studentOrganisation','tbClub'])
    ml_infos = LdapBooleanField(db_column='mlInfos', object_classes=['studentOrganisation'])
    email = LdapCharField(db_column='mlist', object_classes=['studentOrganisation', 'tbClub'])
    website = LdapCharField(db_column='website', object_classes=['studentOrganisation', 'tbClub'])
    description = LdapCharField(db_column='description', object_classes=['studentOrganisation', 'tbClub'])
    logo = LdapCharField(db_column='logo', object_classes=['studentOrganisation', 'tbClub'])
    campagneYear = LdapCharField(db_column='campagneYear', object_classes=['tbCampagne'])


    def __str__(self):
        return str(self.name)

class Association(StudentOrganisation):
    """
    The class having all the element for an asso
    """

    name = LdapCharField(db_column='orgaName', object_classes=['studentOrganisation', 'tbAsso'])
    prezs = LdapListField(db_column='uidPrezs', object_classes=['studentOrganisation','tbAsso'])
    members = LdapListField(db_column='uidMembres', object_classes=['studentOrganisation','tbAsso'])
    ml_infos = LdapBooleanField(db_column='mlInfos', object_classes=['studentOrganisation'])
    email = LdapCharField(db_column='mlist', object_classes=['studentOrganisation', 'tbAsso'])
    website = LdapCharField(db_column='website', object_classes=['studentOrganisation', 'tbAsso'])
    description = LdapCharField(db_column='description', object_classes=['studentOrganisation', 'tbAsso'])
    logo = LdapCharField(db_column='logo', object_classes=['studentOrganisation', 'tbAsso'])

class ListeCampagne(StudentOrganisation):
    """
    The class having all the element for a liste
    """

    # studentOrganisation
    name = LdapCharField(db_column='orgaName', object_classes=['studentOrganisation', 'tbCampagne'])
    prezs = LdapListField(db_column='uidPrezs', object_classes=['studentOrganisation','tbCampagne'])
    members = LdapListField(db_column='uidMembres', object_classes=['studentOrganisation','tbCampagne'])
    ml_infos = LdapBooleanField(db_column='mlInfos', object_classes=['studentOrganisation'])
    email = LdapCharField(db_column='mlist', object_classes=['studentOrganisation', 'tbCampagne'])
    website = LdapCharField(db_column='website', object_classes=['studentOrganisation', 'tbCampagne'])
    description = LdapCharField(db_column='description', object_classes=['studentOrganisation', 'tbCampagne'])
    logo = LdapCharField(db_column='logo', object_classes=['studentOrganisation', 'tbCampagne'])
    campagneYear = LdapCharField(db_column='campagneYear', object_classes=['tbCampagne'])
