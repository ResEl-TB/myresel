# coding=utf-8
import inspect
from copy import copy

from django.core.exceptions import ObjectDoesNotExist
from ldap3 import ALL_ATTRIBUTES

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
        search_query = ldap.build_search_query(**kwargs)
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

    def save(self):
        """
        Insert or update the field
        :return:
        """

        # Insert a new object in the database :
        if self.pk is None:
            ldap = Ldap()
            self.pk = ldap.add(self)

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










