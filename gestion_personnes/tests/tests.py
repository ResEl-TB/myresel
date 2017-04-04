# -*- coding: utf-8 -*-
from datetime import datetime
from unittest import skip

from django.core import mail
from django.test import TestCase

from gestion_personnes.async_tasks import send_mails
from gestion_personnes.forms import InscriptionForm, ModPasswdForm
from gestion_personnes.models import LdapUser, LdapOldUser
from gestion_personnes.tests import try_delete_user, try_delete_old_user, create_full_user
from ldapback.models.fields import LdapCharField


class LdapUserTestCase(TestCase):
    def test_new_user(self):
        user = create_full_user()
        try_delete_user(user.uid)
        user.save()

        user_s = LdapUser.get(pk=user.uid)
        self.assertIsInstance(user_s, LdapUser)
        self.assertEqual(user_s.uid, "amanoury")
        self.assertEqual(user_s.first_name, "Alexandre")
        self.assertEqual(user_s.last_name, "Manoury")
        self.assertEqual(user_s.display_name, "Alexandre Manoury")
        self.assertEqual(user_s.postal_address, "Bâtiment I11 Chambre 123 Maisel Télécom Bretagne\n 655, avenue du Technopôle 29280 Plouzané")
        self.assertEqual(user_s.inscr_date, user.inscr_date)
        self.assertListEqual(user_s.cotiz, ["2016"])
        self.assertEqual(user_s.end_cotiz, user.end_cotiz)
        self.assertEqual(user_s.campus, "Brest")
        self.assertEqual(user_s.building, "I11")
        self.assertEqual(user_s.room_number, "123")
        self.assertEqual(user_s.promo, "2020")
        self.assertEqual(user_s.mail, "alexandre.manoury@telecom-bretagne.eu")
        self.assertEqual(user_s.anneeScolaire, "2015")
        self.assertEqual(user_s.mobile, "33676675525")
        self.assertEqual(user_s.option, "Brest")
        self.assertEqual(user_s.formation, "FIG")
        self.assertEqual(user_s.ae_cotiz, "100")
        self.assertEqual(user_s.ae_nature, "liquide")
        self.assertEqual(user_s.n_adherent, "1235667")

        try_delete_user(user.uid)

    def test_only_ResEl(self):
        now = datetime.now()
        now.replace(microsecond=0)
        user = LdapUser()
        user.uid = "amanoury"
        user.first_name = "Alexandre"
        user.last_name = "Manoury"
        user.user_password = "blah"
        user.nt_password = "blah"

        user.display_name = "Alexandre Manoury"
        user.postal_address = "I11 Maisel blah\n blah blah"

        user.inscr_date = now
        user.cotiz = ["2016"]
        user.end_cotiz = now

        try_delete_user(user.uid)
        user.save()

        user_s = LdapUser.get(pk=user.uid)
        self.assertIsInstance(user_s, LdapUser)
        self.assertEqual(user.uid, user_s.uid)
        self.assertIsInstance(user.building, LdapCharField)

        # Now lets add a maisel field :
        user_s.building = "I11"
        user_s.room_number = "203"
        user_s.save()

        user_t = LdapUser.get(pk=user.uid)
        self.assertIsInstance(user_t, LdapUser)
        self.assertEqual(user_t.building, "I11")
        self.assertEqual(user_t.room_number, "203")

    def test_old_user_creation(self):
        try_delete_old_user("amartine")

        old_user = LdapOldUser()
        old_user.uid = "amartine"
        old_user.first_name = "Alexandre"
        old_user.last_name = "Martine"
        old_user.user_password = "blah"

        old_user.save()

        user_s = LdapOldUser.get(pk="amartine")
        self.assertIsInstance(user_s, LdapOldUser)
        self.assertEqual(old_user.last_name, user_s.last_name)


class InscriptionFormTestCase(TestCase):
    def test_get_free_uid_simple(self):
        user = LdapUser()
        user.uid = "mdanakil"
        user.first_name = "Martin"
        user.last_name = "Danakil"
        user.user_password = "blah"

        try_delete_user(user.uid)
        for i in range(1, 10):
            try_delete_user("%s0%i" % (user.uid, i))

        uid = InscriptionForm.get_free_uid(user.first_name, user.last_name)
        self.assertEqual(user.uid, uid)
        user.save()

        uid2 = InscriptionForm.get_free_uid(user.first_name, user.last_name)
        self.assertEqual("mdanakil01", uid2)

    def test_get_free_uid_old(self):
        try_delete_user("amartine")
        try_delete_old_user("amartine")
        try_delete_user("amartine01")
        try_delete_old_user("amartine01")
        old_user = LdapOldUser()
        old_user.uid = "amartine"
        old_user.first_name = "Alexandre"
        old_user.last_name = "Martine"
        old_user.user_password = "blah"

        old_user.save()

        uid = InscriptionForm.get_free_uid(old_user.first_name, old_user.last_name)
        self.assertEqual("amartine01", uid)


class ModPasswdFormTestCase(TestCase):
    def test_passwd_verification(self):
        data = {
            'password': "blah",
            'password_verification': "bloh",
        }
        form = ModPasswdForm(initial=data)
        self.assertFalse(form.is_valid())

        data = {
            'password': "blah",
            'password_verification': "blah",
        }
        form = ModPasswdForm(initial=data)
        self.assertFalse(form.is_valid())


class AsyncTasksTestCase(TestCase):
    """
    Test the functions defined asyncally
    """
    def test_send_mails(self):
        user = create_full_user()
        send_mails(user)

        self.assertEqual(3, len(mail.outbox))
