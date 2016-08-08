# coding=utf-8
"""
Tests methods for the ldap backend
"""
from django.core.exceptions import ObjectDoesNotExist

from ldapback.backend import Ldap
from django.test import TestCase

from ldapback.directory import LdapModel, LdapField, LdapCharField, LdapPasswordField
from myresel import settings


class QueryConstructorTestCase(TestCase):
    def test_simple_build_search_query(self):
        query = Ldap.build_search_query(uid="loic")
        self.assertEqual("(&(uid=loic))", query)

        query = Ldap.build_search_query(uid="martin", promo=2016)
        self.assertIn(query, ("(&(uid=martin)(promo=2016))", "(&(promo=2016)(uid=martin))"))


class LdapModelTestCase(TestCase):
    class DummyModelObject(LdapModel):
        base_dn = "dc=resel,dc=fr"
        object_classes = []
        man = LdapField(db_column="name", pk=True)
        fruit = LdapField(db_column="banana")
        person = LdapField(db_column="thomas")

    class GenericPerson(LdapModel):
        base_dn = settings.LDAP_DN_PEOPLE
        object_classes = ["genericPerson"]

        uid = LdapField(db_column="uid", object_classes=["genericPerson"], pk=True)
        firstname = LdapCharField(db_column="firstname", object_classes=["genericPerson"])
        lastname = LdapCharField(db_column="lastname", object_classes=["genericPerson"])
        password = LdapPasswordField(db_column="userpassword", object_classes=["genericPerson"])

    def test_to_object(self):
        class QueriedObject(object):
            name = "cat"
            banana = "yellow"
            thomas = "delaby"

        class ModelObject(LdapModel):
            username = LdapField(db_column="name", pk=True)
            fruit = LdapField(db_column="banana")
            person = LdapField(db_column="thomas")

        queried_line = QueriedObject()
        queried_object = ModelObject._to_object(queried_line)

        self.assertIsInstance(queried_object, ModelObject)
        self.assertEqual("cat", queried_object.username)
        self.assertEqual("yellow", queried_object.fruit)
        self.assertEqual("delaby", queried_object.person)

    def test_get_fields(self):

        fields = self.DummyModelObject.get_fields()
        self.assertEqual(len(fields), 3)
        for n, f in fields:
            self.assertIsInstance(f, LdapField)
            self.assertIn(n, ['man', 'fruit', 'person'])

    def test_get_pk_field(self):
        field_name, field = self.DummyModelObject.get_pk_field()
        self.assertEqual("man", field_name)
        self.assertEqual(field, self.DummyModelObject.man)
        self.assertNotEqual(field, self.DummyModelObject.fruit)

    def test_generate_pk(self):
        dummy_model = self.DummyModelObject()
        dummy_model.man = "paris"
        pk = dummy_model.generate_pk()
        self.assertEqual("man=paris,dc=resel,dc=fr", pk)

    def test_to_ldap_field(self):
        user = self.GenericPerson()
        user.uid = "lolo"

        uid_ldap = LdapCharField.to_ldap(user.uid)
        firstname_ldap = LdapCharField.to_ldap(user.firstname)
        self.assertEqual("lolo", uid_ldap)
        self.assertEqual("", firstname_ldap)

    # Should disable this test case ^^
    def test_search(self):
        users = self.GenericPerson.search(uid='lcarr')
        self.assertGreater(len(users), 0)
        for u in users:
            self.assertIsInstance(u, self.GenericPerson)
            self.assertEqual("lcarr", u.uid)
            self.assertEqual("uid=lcarr,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", u.pk)

        users = self.GenericPerson.search(uid='aqwxs01edc')
        self.assertEqual(len(users), 0)

    def test_to_ldap(self):
        user = self.GenericPerson()
        user.uid = "uniquidbgt"
        user.firstname = "pablo"
        user.lastname = "picaso"
        user.password = "pass"

        exp_attr = {
            "uid": "uniquidbgt",
            "firstname": "pablo",
            "lastname": "picaso",
            "userpassword": "pass",
        }
        dn, classes, attributes = user.to_ldap()

        self.assertEqual("uid=uniquidbgt,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", dn)
        self.assertListEqual(["genericPerson"], classes)

        self.assertEqual(len(exp_attr), len(attributes))
        for att_name, att_value in attributes.items():
            if att_name == "userpassword":
                continue
            self.assertEqual(exp_attr[att_name], att_value)

    def test_add_search_delete(self):
        user = self.GenericPerson()

        user.uid = "uniquidbgt"
        user.firstname = "pablo"
        user.lastname = "picaso"
        user.password = "piss"

        # Delete old version
        user_s = self.GenericPerson.get(uid=user.uid)
        user_s.delete()

        # Save new version
        user.save()

        user_s = self.GenericPerson.get(uid=user.uid)
        self.assertIsInstance(user_s, self.GenericPerson)

        self.assertEqual(user.pk, user_s.pk)
        self.assertEqual(user.uid, user_s.uid)
        self.assertEqual(user.firstname, user_s.firstname)
        self.assertEqual(user.lastname, user_s.lastname)
        self.assertNotEqual(user.password, user_s.password)

        user_s.delete()

        with self.assertRaises(ObjectDoesNotExist):
            self.GenericPerson.get(uid=user.uid)








