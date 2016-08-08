# coding=utf-8
from ldap3 import Connection, Server

from myresel import settings


class LdapError(Exception):
    pass


class Ldap(object):
    """
    Handle every methods related to the ldap
    """

    def __init__(self):
        self.DB_HOST = settings.LDAP_URL
        self.DB_USER = settings.LDAP_DN_ADMIN
        self.DB_PASSWD = settings.LDAP_PASSWD
        self.DB_SSL = False

    def _new_connection(self):
        """
        Return a new connection to the ResEl, must be unbind after all
        :return:
        """
        return Connection(
            Server(self.DB_HOST, use_ssl=self.DB_SSL),
            user=self.DB_USER,
            password=self.DB_PASSWD,
            auto_bind=True
        )

    def search(self, dn, query, attr=None):
        """
        Perform a research based on the query made
        :param attr:
        :param query:
        :return:
        """
        result = None
        conn = self._new_connection()
        if conn.search(dn, query, attributes=attr):
            result = conn.entries
        conn.unbind()
        return result

    @staticmethod
    def build_search_query(**kwargs):
        """
        Build a query based on the kwargs.
        For the moment it is a simple `and` between them
        One day we might do something better
        :param karg:
        :return:
        """
        query = "(&"
        for name, value in kwargs.items():
            query += "(" + str(name) + "=" + str(value) + ")"
        query += ")"
        return query

    def add(self, model):
        """
        Insert an object in database
        :param model:
        :return:
        """
        pk, object_class, attributes = model.to_ldap()
        conn = self._new_connection()
        v = conn.add(pk, object_class, attributes)
        conn.unbind()
        return pk

    def update(self, model):
        """
        Perform an update of the object in the database
        :param model:
        :return:
        """
        pk_field_name, _ = model.get_pk_field()
        pk = getattr(model, pk_field_name)

        old_model = model.__class__.get(pk=pk)

        diff = model.ldap_diff(old_model)
        conn = self._new_connection()
        v = conn.modify(old_model.pk, diff)
        conn.unbind()
        if not v:
            raise LdapError(str(conn.result))


    def delete(self, model):
        """
        Delete a model and all its attributes from the db
        :param model:
        :return:
        """
        pk = model.pk
        conn = self._new_connection()
        conn.delete(pk)
        conn.unbind()