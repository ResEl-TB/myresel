# coding=utf-8
import inspect

from django.core.exceptions import ObjectDoesNotExist
from ldap3 import ALL_ATTRIBUTES, MODIFY_REPLACE, LDAPAttributeError, ALL_OPERATIONAL_ATTRIBUTES

from ldapback.backends.ldap.base import Ldap
from ldapback.models.fields import LdapField


# TODO: create an init function to initalize fields to the right type

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
    def filter(cls, **kwargs):
        """
        Filter a query according to the asked arguments
        :param kwargs:
        :return:
        """
        new_kwargs = {}
        for arg, arg_value in kwargs.items():
            new_arg = arg
            arg_value = arg_value if arg_value is not None else ""
            new_arg_value = Ldap.sanitize(arg_value)
            arg_splited = arg.split("__")
            if len(arg_splited) > 1:
                new_arg, matching_type = arg_splited
                if matching_type == "contains":
                    new_arg_value = "*" + arg_value + "*"
                elif matching_type == "startswith":
                    new_arg_value = arg_value + "*"
                elif matching_type == "endswith":
                    new_arg_value = "*" + arg_value
            new_kwargs[new_arg] = new_arg_value
        return cls._search(**new_kwargs)

    @classmethod
    def all(cls):
        """
        Return all entries in base_dn
        :return:
        """
        ldap = Ldap()

        search_results = ldap.search(cls.base_dn, '(!(objectClass=organizationalUnit))', attr=ALL_ATTRIBUTES)
        if search_results is None:
            return []

        results = []
        for result_line in search_results:
            results.append(cls._to_object(result_line))
        return results

    @classmethod
    def all(cls):
        """
        Return all entries in base_dn
        :return:
        """
        ldap = Ldap()

        search_results = ldap.search(cls.base_dn, '(!(objectClass=organizationalUnit))', attr=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES])
        if search_results is None:
            return []

        results = []
        for result_line in search_results:
            results.append(cls._to_object(result_line))
        return results

    @classmethod
    def _search(cls, **kwargs):
        """
        Perform a search in the ldap
        :return:
        """
        ldap = Ldap()
        search_args = {}

        # Convert search query into db_column search query
        for arg, arg_value in kwargs.items():
            if arg == "pk":
                arg = cls.get_pk_field()[1].db_column  # TODO : THIS IS MOCHE, redéfinition de args pour quelque chose de sémentiquement différent
                search_args[arg] = arg_value
            else:
                arg = getattr(cls, arg).db_column
                search_args[arg] = arg_value
        search_query = ldap.build_search_query(**search_args)
        search_results = ldap.search(cls.base_dn, search_query, attr=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES])
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
            try:
                retrieved_value = field.from_ldap(getattr(line, column_name))
            except LDAPAttributeError:
                retrieved_value = field.from_ldap("")
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
        results = cls.filter(**kwargs)
        if len(results) == 0:
            raise ObjectDoesNotExist("Could not find the requested object")
        return results[0]

    def generate_pk(self):
        """
        Return a correct uid or pk for the object
        :return:
        """

        pk_field_name, pk_field = self.get_pk_field()
        pk_field_value = str(getattr(self, pk_field_name))
        if len(pk_field_value) == 0:
            raise ValueError("Empty pk value")
        pk = "%s=%s,%s" % (pk_field.db_column, pk_field_value, self.base_dn)
        return pk

    def __eq__(self, other):
        return (other.__class__ == self.__class__ and
             other.pk == self.pk
        )

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

        viewed_object_classes = set()

        diff = {}
        for field_name, field in fields:
            db_column = field.db_column
            old_val = getattr(other, field_name)
            new_val = getattr(self, field_name)
            field_diff = field.calc_diff(old_val, new_val)
            if field_diff is not None:
                diff_type, diff_val = field_diff
                viewed_object_classes = viewed_object_classes.union(set(field.object_classes))
                if isinstance(diff_val, list):
                    diff[db_column] = [(diff_type, diff_val)]
                else:
                    diff[db_column] = [(diff_type, [diff_val])]
            elif field.to_ldap(new_val) != "":
                viewed_object_classes = viewed_object_classes.union(set(field.object_classes))

        # update object class
        diff['objectClass'] = [(MODIFY_REPLACE, list(viewed_object_classes))]
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
            ldap.update(self)

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
