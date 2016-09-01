# coding=utf-8
from datetime import datetime

from ldap3 import MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE

from fonctions.generic import hash_passwd, hash_to_ntpass


# TODO : Fields to implement
# Numeric fields
# Bool field


class LdapField(object):
    __wrap__ = str
    def __init__(self, db_column=None, object_classes=None, required=False, pk=False):
        if db_column is None:
            raise AttributeError("No db_column given")
        self.db_column = db_column
        if object_classes is None:
            self.object_classes = []
        else:
            self.object_classes = object_classes

        self.is_pk = pk
        self.required = required or pk

    def to_ldap(self, obj):
        """
        Method to convert to a friendly type for the ldap
        Return empty string if the field is not defined
        :param obj:
        :return:
        """
        # If the obj is an instance of this, it means that it is not init
        ldap_str = ""
        if isinstance(obj, self.__class__):
            ldap_str = ""
        else:
            ldap_str = str(obj)

        if self.required and ldap_str == "":
            raise ValueError("Field %s is cannot be empty" % self.__class__)
        return ldap_str

    @classmethod
    def from_ldap(cls, obj):
        """
        Method to convert an ldap field to a friendly
        human type
        :param obj:
        :return:
        """
        return str(obj)

    def calc_diff(self, old, new):
        """
        Return an ldap compliant diff
        returns None if there is no diff
        :param old:
        :param new:
        :return:
        """
        old_ldap = self.to_ldap(old)
        new_ldap = self.to_ldap(new)
        if old_ldap == new_ldap:
            return None

        if old_ldap == "":
            edit_type = MODIFY_ADD
        elif new_ldap == "":
            edit_type = MODIFY_DELETE
        else:
            edit_type = MODIFY_REPLACE

        return edit_type, new_ldap


class LdapCharField(LdapField):
    pass


class LdapPasswordField(LdapCharField):

    def to_ldap(self, obj):
        pwd = super().to_ldap(obj)

        if pwd == "":
            return pwd

        return hash_passwd(pwd)


class LdapNtPasswordField(LdapCharField):

    def to_ldap(self, obj):
        pwd = super().to_ldap(obj)

        if pwd == "":
            return pwd

        return hash_to_ntpass(pwd)


class LdapListField(LdapField):

    def to_ldap(self, obj):
        ldap_value = ""
        if isinstance(obj, self.__class__):
            ldap_value = ""
        elif len(obj) == 0:
            ldap_value = ""
        else:
            ldap_value = obj

        if self.required and len(ldap_value) == 0:
            raise ValueError("Field %s is cannot be empty" % self.__class__)

        return ldap_value

    @classmethod
    def from_ldap(cls, obj):
        lst = super().from_ldap(obj)
        if lst == "":
            return []
        return [o for o in obj]

class LdapDatetimeField(LdapField):
    """
    A ldap field that is a wrapper of the python datetime field
    """
    __wrap__ = datetime

    def to_ldap(self, obj):
        ldap_value = ""
        if isinstance(obj, self.__class__):
            ldap_value = ""
        elif obj == None:
            ldap_value = ""
        else:
            ldap_value = obj.strftime('%Y%m%d%H%M%S') + 'Z'

        if self.required and len(ldap_value) == 0:
            raise ValueError("Field %s is cannot be empty" % self.__class__)

        return ldap_value

    @classmethod
    def from_ldap(cls, obj):
        obj = super().from_ldap(obj)
        if obj == "":
            return None
        return datetime.strptime(obj, '%Y%m%d%H%M%SZ')