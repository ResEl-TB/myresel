# coding=utf-8
from ldap3 import MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE

from fonctions.generic import hash_passwd, hash_to_ntpass

# TODO : Fields to implement
# Numeric fields
# Bool field


class LdapField(object):
    def __init__(self, db_column=None, object_classes=None, pk=False):
        if db_column is None:
            raise AttributeError("No db_column given")
        self.db_column = db_column
        if object_classes is None:
            self.object_classes = []
        else:
            self.object_classes = object_classes

        self.is_pk = pk

    @classmethod
    def to_ldap(cls, obj):
        """
        Method to convert to a friendly type for the ldap
        Return empty string if the field is not defined
        :param obj:
        :return:
        """
        # If the obj is an instance of this, it means that it is not init
        if isinstance(obj, cls):
            return ""

        return str(obj)

    @classmethod
    def from_ldap(cls, obj):
        """
        Method to convert an ldap field to a friendly
        human type
        :param obj:
        :return:
        """
        return str(obj)

    @classmethod
    def calc_diff(cls, old, new):
        """
        Return an ldap compliant diff
        returns None if there is no diff
        :param old:
        :param new:
        :return:
        """
        old_ldap = cls.to_ldap(old)
        new_ldap = cls.to_ldap(new)
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
    @classmethod
    def to_ldap(cls, obj):
        pwd = super().to_ldap(obj)

        if pwd == "":
            return pwd

        return hash_passwd(pwd)


class LdapNtPasswordField(LdapCharField):
    @classmethod
    def to_ldap(cls, obj):
        pwd = super().to_ldap(obj)

        if pwd == "":
            return pwd

        return hash_to_ntpass(pwd)


class LdapListField(LdapField):

    @classmethod
    def to_ldap(cls, obj):
        if isinstance(obj, cls):
            return ""
        if len(obj) == 0:
            return ""
        return obj

    @classmethod
    def from_ldap(cls, obj):
        lst = super().from_ldap(obj)
        if lst == "":
            return []
        return [o for o in obj]
