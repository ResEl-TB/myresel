# coding=utf-8
"""
Tests methods for the ldap backend
"""
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from ldapback.backends.ldap.base import Ldap
from ldapback.models.base import LdapModel
from ldapback.models.fields import LdapField, LdapCharField, LdapPasswordField, LdapListField
from myresel import settings

# TODO: test when python name and ldap fields names are different


# Declare some classes for the test
class DummyModelObject(LdapModel):
    base_dn = "dc=resel,dc=fr"
    object_classes = []
    man = LdapField(db_column="name", pk=True)
    fruit = LdapField(db_column="banana")
    person = LdapField(db_column="thomas")


class TestGenericPerson(LdapModel):
    base_dn = settings.LDAP_DN_PEOPLE
    object_classes = ["genericPerson", "enstbPerson"]

    # genericPerson
    uid = LdapField(db_column="uid", object_classes=["genericPerson"], pk=True, required=True)
    firstname = LdapCharField(db_column="firstname", object_classes=["genericPerson"], required=True)
    lastname = LdapCharField(db_column="lastname", object_classes=["genericPerson"], required=True)
    password = LdapPasswordField(db_column="userpassword", object_classes=["genericPerson"], required=True)

    # enstbPerson
    promo = LdapCharField(db_column="promo", object_classes=["enstbPerson"])
    altMail = LdapListField(db_column="altMail", object_classes=["enstbPerson"])


class QueryConstructorTestCase(TestCase):
    def test_simple_build_search_query(self):
        query = Ldap.build_search_query(uid="loic")
        self.assertEqual("(&(uid=loic))", query)

        query = Ldap.build_search_query(uid="martin", promo=2016)
        self.assertIn(query, ("(&(uid=martin)(promo=2016))", "(&(promo=2016)(uid=martin))"))


def try_delete_user(uid):
    try:
        user_s = TestGenericPerson.get(pk=uid)
        user_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


class LdapModelTestCase(TestCase):
    def setUp(self):
        try_delete_user("lcarr")
        user = TestGenericPerson()
        user.uid = "lcarr"
        user.firstname = "Loïc"
        user.lastname = "Carr"
        user.password = "123zizou"

        user.promo = 2018
        user.altMail = "loic.carr@telecom-bretagne.eu"
        user.save()


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

        fields = DummyModelObject.get_fields()
        self.assertEqual(len(fields), 3)
        for n, f in fields:
            self.assertIsInstance(f, LdapField)
            self.assertIn(n, ['man', 'fruit', 'person'])

    def test_get_pk_field(self):
        field_name, field = DummyModelObject.get_pk_field()
        self.assertEqual("man", field_name)
        self.assertEqual(field, DummyModelObject.man)
        self.assertNotEqual(field, DummyModelObject.fruit)

    def test_generate_pk(self):
        dummy_model = DummyModelObject()
        dummy_model.man = "paris"
        pk = dummy_model.generate_pk()
        self.assertEqual("name=paris,dc=resel,dc=fr", pk)

    def test_to_ldap_field(self):
        user = TestGenericPerson()
        user.uid = "lolo"

        uid_ldap = TestGenericPerson.uid.to_ldap(user.uid)
        promo_ldap = TestGenericPerson.promo.to_ldap(user.firstname)
        self.assertEqual("lolo", uid_ldap)
        self.assertEqual("", promo_ldap)

    # Should disable this test case ^^
    def test_search(self):
        users = TestGenericPerson.search(uid='lcarr')
        self.assertGreater(len(users), 0)
        for u in users:
            self.assertIsInstance(u, TestGenericPerson)
            self.assertEqual("lcarr", u.uid)
            self.assertEqual("uid=lcarr,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", u.pk)

        users = TestGenericPerson.search(uid='aqwxs01edc')
        self.assertEqual(len(users), 0)

    def test_get(self):
        user = TestGenericPerson.get(uid='lcarr')

        self.assertIsInstance(user, TestGenericPerson)
        self.assertEqual("lcarr", user.uid)
        self.assertEqual("uid=lcarr,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", user.pk)

        user = TestGenericPerson.get(pk='lcarr')

        self.assertIsInstance(user, TestGenericPerson)
        self.assertEqual("lcarr", user.uid)
        self.assertEqual("uid=lcarr,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", user.pk)

    def test_to_ldap(self):
        user = TestGenericPerson()
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
        user = TestGenericPerson()

        user.uid = "uniquidbgt"
        user.firstname = "pablo"
        user.lastname = "picaso"
        user.password = "piss"

        # Delete old version
        try_delete_user(user.uid)

        # Save new version
        user.save()

        user_s = TestGenericPerson.get(uid=user.uid)
        self.assertIsInstance(user_s, TestGenericPerson)

        self.assertEqual(user.pk, user_s.pk)
        self.assertEqual(user.uid, user_s.uid)
        self.assertEqual(user.firstname, user_s.firstname)
        self.assertEqual(user.lastname, user_s.lastname)
        self.assertNotEqual(user.password, user_s.password)

        user_s.delete()

        with self.assertRaises(ObjectDoesNotExist):
            TestGenericPerson.get(uid=user.uid)

    def test_update(self):
        try_delete_user("uniquiabga")

        user = TestGenericPerson()

        user.uid = "uniquiabga"
        user.firstname = "pablo"
        user.lastname = "picaso"
        user.password = "puss"

        user.save()

        # user.password = "piass"
        user.firstname = "pablio"
        user.lastname = "pakito"

        user.save()

        user_s = TestGenericPerson.get(uid=user.uid)

        self.assertEqual(user.firstname, "pablio")
        self.assertEqual(user.lastname, "pakito")

        user_s.delete()


class LdapFieldTestCase(TestCase):
    def new_user(self):
        user = TestGenericPerson()
        user.uid = "fdshtlz"
        user.firstname = "Martin"
        user.lastname = "Thomas"
        user.password = "Blah"

        user.promo = "2020"
        user.altMail = ['martin.thomas@t.com', 'thomas.martin@t.com']

        try_delete_user(user.uid)
        return user

    def test_list_field_add(self):
        user = self.new_user()
        user.save()

        user_s = TestGenericPerson.get(pk=user.uid)
        self.assertIsInstance(user_s, TestGenericPerson)
        self.assertIsInstance(user_s.altMail, list)
        self.assertListEqual(user.altMail, user_s.altMail)

    def test_empty_list_field(self):
        user = self.new_user()
        user.altMail = []
        user.save()

        user_s = TestGenericPerson.get(pk=user.uid)
        self.assertIsInstance(user_s, TestGenericPerson)
        self.assertIsInstance(user_s.altMail, list)
        self.assertListEqual(user.altMail, [])

    def test_list_field_edit(self):
        user = self.new_user()
        user.save()

        user_s = TestGenericPerson.get(pk=user.uid)
        self.assertIsInstance(user_s, TestGenericPerson)
        self.assertIsInstance(user_s.altMail, list)
        self.assertListEqual(user.altMail, user_s.altMail)

        user_s.altMail.append('remy.martin.com')
        user_s.save()

        user_t = TestGenericPerson.get(pk=user.uid)
        self.assertIsInstance(user_t, TestGenericPerson)
        self.assertIsInstance(user_t.altMail, list)
        self.assertListEqual(user_s.altMail, user_t.altMail)

    def test_default_required(self):
        user = TestGenericPerson()
        user.uid = "fdshtlz"

        user.promo = "2020"
        user.altMail = ['martin.thomas@t.com', 'thomas.martin@t.com']

        with self.assertRaises(ValueError):
            user.save()
