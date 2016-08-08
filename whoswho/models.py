from django.db import models

from ldapback.backends.ldap.base import Ldap
from ldapback.models.base import LdapModel
from ldapback.models.fields import LdapField, LdapCharField, LdapPasswordField, LdapListField

from myresel import settings

class UserModel(LdapModel):
    base_dn = settings.LDAP_DN_PEOPLE
    object_classes = ["genericPerson", "enstbPerson"]
        
    uid = LdapField(db_column="uid", object_classes=["genericPerson"], pk=True)
    firstname = LdapCharField(db_column="firstname", object_classes=["genericPerson"])
    lastname = LdapCharField(db_column="lastname", object_classes=["genericPerson"])
    promo = LdapField(db_column="promo", object_classes=["enstbPerson"])
