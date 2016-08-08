# coding=utf-8
import inspect
from copy import copy

from django.core.exceptions import ObjectDoesNotExist
from ldap3 import ALL_ATTRIBUTES, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE

from ldapback.backend import Ldap

from fonctions.generic import hash_passwd, hash_to_ntpass


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


class LdapModel(object):
    """
    A Model is related to a dn
    """
    base_dn = ""
    object_classes = []
    pk = None

    class ObjectDoesNotExist(Exception):
        pass

    @classmethod
    def search(cls, **kwargs):
        """
        Perform a search in the ldap
        :return: 
        """
        ldap = Ldap()
        search_args = {}

        # Convert search query into db_column search query
        for arg, arg_value in kwargs.items():
            if arg == "pk":
                arg = cls.get_pk_field()[1].db_column
                search_args[arg] = arg_value
            else:
                arg = getattr(cls, arg).db_column
                search_args[arg] = arg_value
        search_query = ldap.build_search_query(**search_args)
        search_results = ldap.search(cls.base_dn, search_query, attr=ALL_ATTRIBUTES)
        if search_results is None:
            return []

        results = []
        for result_line in search_results:
            results.append(cls._to_object(result_line))
        return results

    @classmethod
    def _to_object(cls, line):
        model = cls()
        attributes = cls.get_fields()

        for field_name, field in attributes:
            column_name = field.db_column
            retrieved_value = field.from_ldap(getattr(line, column_name))
            setattr(model, field_name, retrieved_value)
            if field.is_pk:
                model.pk = model.generate_pk()  # TODO: maybe authorise only some fields as pk

        return model

    @classmethod
    def get_fields(cls):
        """
        Get all the ldap fields of a LdapModel
        :return: Returns a tuple ((field_name, field), ...)
        """
        return inspect.getmembers(
            cls,
            lambda a: not (inspect.isroutine(a)) and issubclass(a.__class__, LdapField)
        )

    @classmethod
    def get_pk_field(cls):
        fields = cls.get_fields()
        for n, f in fields:
            if f.is_pk:
                return n, f

    @classmethod
    def get(cls, **kwargs):
        results = cls.search(**kwargs)
        if len(results) == 0:
            raise ObjectDoesNotExist("Could not find the requested object")
        return results[0]

    def generate_pk(self):
        """
        Return a correct uid or pk for the object
        :return:
        """

        pk_field_name, _ = self.get_pk_field()
        pk_field_value = str(getattr(self, pk_field_name))
        if len(pk_field_value) == 0:
            raise ValueError("Empty pk value")
        pk = "%s=%s,%s" % (pk_field_name, pk_field_value, self.base_dn)
        return pk

    def to_ldap(self):
        """
        Convert this object to an ldap compliant tuple
        :return:
        """
        fields = self.get_fields()
        attributes = {}
        if self.pk is not None:
            dn = self.pk
        else:
            dn = self.generate_pk()

        viewed_object_classes = set()

        for field_name, field in fields:
            db_name = field.db_column
            value = getattr(self, field_name)
            ldap_value = field.to_ldap(value)
            if len(ldap_value) > 0:
                viewed_object_classes = viewed_object_classes.union(set(field.object_classes))
                attributes[db_name] = ldap_value

        classes = list(viewed_object_classes)
        return dn, classes, attributes

    def ldap_diff(self, other):
        """
        Return an Ldap diff between another object and this one
        This one is considered as the new one
        - Changes is a dictionary in the form {'attribute1': change),
        'attribute2': [change, change, ...], ...}
        change is (operation, [value1, value2, ...])
        - Operation is 0 (MODIFY_ADD), 1 (MODIFY_DELETE), 2 (MODIFY_REPLACE), 3 (MODIFY_INCREMENT)

        :param other:
        :return: dict
        """
        fields = self.get_fields()

        diff = {}
        for field_name, field in fields:
            db_column = field.db_column
            old_val = getattr(other, field_name)
            new_val = getattr(self, field_name)

            field_diff = field.calc_diff(old_val, new_val)
            if field_diff is not None:
                diff_type, diff_val = field_diff
                diff[db_column] = [(diff_type, [diff_val])]

        return diff

    def save(self):
        """
        Insert or update the field
        :return:
        """

        # Insert a new object in the database :
        ldap = Ldap()
        if self.pk is None:
            self.pk = ldap.add(self)
        else:
            self.pk = ldap.update(self)

    def delete(self):
        """
        Delete the object from the database
        :return:
        """
        if self.pk is not None:
            ldap = Ldap()
            ldap.delete(self)
        else:
            raise ObjectDoesNotExist("This object is not in database")










