# -*- coding: utf-8 -*-
"""
Test the views in the current module
"""
import datetime

from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.test import TestCase

from fonctions.generic import hash_to_ntpass, compare_passwd
from gestion_personnes.models import LdapUser, UserMetaData
from gestion_personnes.tests import try_delete_user, create_full_user
from gestion_personnes.views import MailResEl
from myresel import settings


class InscriptionCase(TestCase):
    def setUp(self):
        try_delete_user("lcarr")

    def test_simple(self):
        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95", ZONE="Brest-any")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.199", ZONE="Brest-any")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

    def test_full_signup(self):
        user = create_full_user(email="dsqfsdfjnsdfs@fdsfsdf.qsd")
        try_delete_user(user.uid)

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95", ZONE="Brest-any")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

        r = self.client.post(reverse(
            "gestion-personnes:inscription"),
            data={
                'last_name': user.last_name,
                'first_name': user.first_name,
                'category': user.category,
                'formation': user.formation,
                'email': user.mail,
                'email_verification': user.mail,
                'password': user.user_password,
                'password_verification': user.user_password,
                'campus': user.campus,
                'building': user.building,
                'room': user.room_number,
                'birth_place': user.birth_place,
                'birth_country': user.birth_country,
                'birth_date': user.freeform_birth_date,
                'phone': user.mobile,
                'certify_truth': 'certify_truth',
            },
            HTTP_HOST="10.0.3.95", ZONE="Brest-any", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/cgu.html')

        r = self.client.post(
            reverse("gestion-personnes:cgu"),
            data={
                'have_read': 'have_read'
            },
            HTTP_HOST="10.0.3.95", ZONE="Brest-any", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/finalize_signup.html')
        self.assertContains(r, user.uid)

        user_s = LdapUser.get(pk=user.uid)
        self.assertEqual(user.uid, user_s.uid)
        self.assertEqual(user.first_name, user_s.first_name)
        self.assertEqual(user.last_name, user_s.last_name)
        self.assertEqual(user.building, user_s.building)
        self.assertEqual(user.campus, user_s.campus)
        self.assertEqual(user.end_cotiz.date(), user_s.end_cotiz.date())
        self.assertEqual(user.employee_type, user_s.employee_type)

        # TODO: find a way to check if emails are sent...
        # get_worker().work(burst=True)
        # self.assertEqual(3, len(mail.outbox))

    def test_maisel_signup(self):
        user = create_full_user(email="maisel@emplo.yee")
        try_delete_user(user.uid)

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95", ZONE="Brest-any")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

        r = self.client.post(reverse(
            "gestion-personnes:inscription"),
            data={
                'last_name': user.last_name,
                'first_name': user.first_name,
                'category': "maisel",
                'formation': "",
                'email': user.mail,
                'email_verification': user.mail,
                'password': user.user_password,
                'password_verification': user.user_password,
                'campus': "None",
                'building': "",
                'room': "",
                'address': "Some address",
                'birth_place': user.birth_place,
                'birth_country': user.birth_country,
                'birth_date': user.freeform_birth_date,
                'phone': user.mobile,
                'certify_truth': 'certify_truth',
            },
            HTTP_HOST="10.0.3.95", ZONE="Brest-any", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/cgu.html')

        r = self.client.post(
            reverse("gestion-personnes:cgu"),
            data={
                'have_read': 'have_read'
            },
            HTTP_HOST="10.0.3.95", ZONE="Brest-any", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/finalize_signup.html')
        self.assertContains(r, user.uid)

        user_s = LdapUser.get(pk=user.uid)
        self.assertEqual(user.uid, user_s.uid)
        self.assertEqual(user.first_name, user_s.first_name)
        self.assertEqual(user.last_name, user_s.last_name)
        self.assertEqual(user_s.employee_type, "staff")

    def test_wrong_email(self):
        user = create_full_user(email="sdlfskdfjh@hotmail.com")
        try_delete_user(user.uid)

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95", ZONE="Brest-any")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

        r = self.client.post(reverse(
            "gestion-personnes:inscription"),
            data={
                'last_name': user.last_name,
                'first_name': user.first_name,
                'category': user.category,
                'formation': user.formation,
                'email': "sdlfskdfjh@hotmail.com",
                'email_verification': "sdlfskdfjh@hotmail.com",
                'password': user.user_password,
                'password_verification': user.user_password,
                'campus': user.campus,
                'building': user.building,
                'room': user.room_number,
                'birth_place': user.birth_place,
                'birth_country': user.birth_country,
                'birth_date': user.freeform_birth_date,
                'phone': user.mobile,
                'certify_truth': 'certify_truth',
            },
            HTTP_HOST="10.0.3.95", ZONE="Brest-any", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/inscription.html')
        self.assertContains(r, "Les adresses e-mail du domaine hotmail.com ne sont pas autorisées")



class ModPasswdCase(TestCase):
    def setUp(self):
        try_delete_user("lcarr")

        user = LdapUser()
        user.uid = 'lcarr'
        user.first_name = "Loïc"
        user.last_name = "Carr"
        user.user_password = "blah"
        user.nt_password = user.user_password
        user.save()

        self.client.login(username="lcarr", password="blah")

    def test_simple_mod_passwd(self):
        r = self.client.get(reverse("gestion-personnes:mod-passwd"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, r.status_code)

        r = self.client.post(
            reverse("gestion-personnes:mod-passwd"),
            data={
                'password': 'blohhhhhhh',
                'password_verification': 'blohhhhhhh'
            },
            HTTP_HOST="10.0.3.95",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        u = LdapUser.get(pk="lcarr")
        self.assertEqual("{NT}" + hash_to_ntpass("blohhhhhhh"), u.nt_password)
        self.assertTrue(compare_passwd("blohhhhhhh", u.user_password))

    def test_wrong_mod_passwd(self):
        r = self.client.get(reverse("gestion-personnes:mod-passwd"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, r.status_code)

        r = self.client.post(
            reverse("gestion-personnes:mod-passwd"),
            data={
                'password': 'blohhhhhhh',
                'password_verification': 'bluhhhhhhh'
            },
            HTTP_HOST="10.0.3.95",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        u = LdapUser.get(pk="lcarr")
        self.assertEqual("{NT}" + hash_to_ntpass("blah"), u.nt_password)
        # self.assertEqual(hash_passwd("blah"), u.user_password)  # commented because I don't know how to check the passwd

    def test_passwd_too_short(self):
        r = self.client.post(
            reverse("gestion-personnes:mod-passwd"),
            data={
                'password': 'bloh',
                'password_verification': 'bloh'
            },
            HTTP_HOST="10.0.3.95",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        u = LdapUser.get(pk="lcarr")
        self.assertEqual("{NT}" + hash_to_ntpass("blah"), u.nt_password)
        # self.assertEqual(hash_passwd("blah"), u.user_password)


class TestPersonalInfo(TestCase):
    def setUp(self):
        try_delete_user("lcarr")

        user = LdapUser()
        user.uid = 'lcarr'
        user.first_name = "Loïc"
        user.last_name = "Carr"
        user.mail = "lcarr@gmail.com"
        user.user_password = "blah"
        user.promo = "2018"
        user.inscr_date = datetime.datetime.now().astimezone()
        user.nt_password = user.user_password
        user.save()

        self.client.login(username="lcarr", password="blah")

    def test_simple_mod(self):
        r = self.client.get(reverse("gestion-personnes:personal-infos"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/personal_info.html")

        r = self.client.post(
            reverse("gestion-personnes:personal-infos"),
            data={
                'email': "email@email.fr",
                'phone': "0123456789",
                'campus': "Brest",
                'building': "I10",
                'room': "14",
                'certify_truth': "certify_truth"
        },
            HTTP_HOST="10.0.3.99",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        self.assertContains(r, "Vos informations ont bien été mises à jour.")
        u = LdapUser.get(pk="lcarr")
        self.assertEqual(u.mail, "email@email.fr")
        self.assertEqual(u.mobile, "+33123456789")
        self.assertEqual(u.campus, "Brest")
        self.assertEqual(u.building, "I10")
        self.assertEqual(u.room_number, "14")

        # Test a bug which would modify wrongly the password
        self.assertTrue(compare_passwd("blah", u.user_password))


class TestResetPasswd(TestCase):
    def setUp(self):
        self.user = create_full_user()
        self.old_pwd = self.user.user_password
        try_delete_user(self.user.uid)
        self.user.save()

    def test_simple_init(self):
        new_pwd = "blahblahcar"
        r = self.client.get(reverse("gestion-personnes:reset-pwd-send"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed("gestion_personnes/reset_pwd_send.html")

        r = self.client.post(
            reverse("gestion-personnes:reset-pwd-send"),
            data={
                'uid': self.user.uid
            },
            HTTP_HOST="10.0.3.94",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertContains(r, "Nous venons de vous envoyer un e-mail")

        self.assertEqual(1, len(mail.outbox))

        m = mail.outbox[0]
        link = m.body.split('\n')[3]
        r = self.client.get(link, HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)

        r = self.client.post(
            link,
            data={
                'password': new_pwd,
                'password_verification': new_pwd,
            },
            HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")

        logged = self.client.login(username=self.user.uid, password=new_pwd)
        self.assertTrue(logged)


class TestSendUid(TestCase):
    def setUp(self):
        self.user = create_full_user()
        self.old_pwd = self.user.user_password
        try_delete_user(self.user.uid)
        self.user.save()

    def test_simple_send(self):
        r = self.client.get(reverse("gestion-personnes:send-uid"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/get_uid_from_email.html")

        r = self.client.post(
            reverse("gestion-personnes:send-uid"),
            data={
                'email': self.user.mail
            },
            HTTP_HOST="10.0.3.94",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertContains(r, "Nous venons de vous envoyer un e-mail")

        self.assertEqual(1, len(mail.outbox))

        m = mail.outbox[0]
        self.assertIn(self.user.mail, m.to)

    def test_assert_wrong_email(self):
        r = self.client.post(
            reverse("gestion-personnes:send-uid"),
            data={
                'email': "blahbloh" + self.user.mail
            },
            HTTP_HOST="10.0.3.94",
            follow=True
        )

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/get_uid_from_email.html")
        self.assertContains(r, "error")


class TestCheckEmail(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)
        self.user.save()

        self.client.login(username=self.user.uid, password=self.user.user_password)

    def test_simple_check(self):
        r = self.client.get(reverse("gestion-personnes:check-email"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertContains(r, "Nous venons de vous envoyer un e-mail")

        self.assertEqual(1, len(mail.outbox))
        m = mail.outbox[0]
        link = m.body.split('\n')[3]
        r = self.client.get(link, HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")

        user_s = UserMetaData.objects.get(uid=self.user.uid)
        self.assertTrue(user_s.email_validated)

class MailResElViewCase(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)
        self.user.save()

        self.client.login(username=self.user.uid, password=self.user.user_password)

    def test_simple_mail_creation(self):
        r = self.client.get(reverse("gestion-personnes:mail"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/mail_resel_new.html")
        self.assertContains(r, "alexandre.manoury@resel.fr")

        r = self.client.post(
            reverse("gestion-personnes:mail"),
            HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/mail_resel.html")
        self.assertEqual(1, len(mail.outbox))

        user_n = LdapUser.get(uid=self.user.uid)
        self.assertEqual(user_n.uid + '/Maildir/', user_n.mail_dir)
        self.assertEqual('/var/mail/virtual/'+user_n.uid, user_n.home_directory)
        self.assertTrue("mailPerson" in user_n.object_classes)

    def test_already_existing_mail_creation(self):
        # Create a fake user
        mv = MailResEl()
        h = mv.build_address(self.user.uid, self.user.first_name, self.user.last_name)
        self.user.mail_local_address = h + '@resel.fr'
        self.user.mail_dir = self.user.uid + '/Maildir/'
        self.user.mail_del_date = None
        self.user.home_directory = '/var/mail/virtual/' + self.user.uid
        self.user.object_classes = ['mailPerson']
        self.user.save()

        r = self.client.get(reverse("gestion-personnes:mail"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)

        # Better way to detect an error ?
        self.assertTemplateUsed(r, "gestion_personnes/mail_resel.html")

    def test_build_address(self):
        # TODO : do a bit more tests
        mv = MailResEl()
        self.assertEqual("loic.carr", mv.build_address("lcarr", "Loïc", "Carr"))

class DeleteMailResElViewCase(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)

        # Create a fake user
        mv = MailResEl()
        h = mv.build_address(self.user.uid, self.user.first_name, self.user.last_name)
        self.user.mail_local_address = h + '@resel.fr'
        self.user.mail_dir = self.user.uid + '/Maildir/'
        self.user.mail_del_date = None
        self.user.home_directory = '/var/mail/virtual/' + self.user.uid
        self.user.object_classes = ['mailPerson']
        self.user.save()

        self.client.login(username=self.user.uid, password=self.user.user_password)

    def test_simple_delete_mail(self):
        r = self.client.get(reverse("gestion-personnes:delete-mail"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/delete_mail.html")

        r = self.client.post(
            reverse("gestion-personnes:delete-mail"),
            data={
                "delete_field": self.user.mail_local_address,
            },
            HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/mail_resel_new.html")

        user_n = LdapUser.get(uid=self.user.uid)
        self.assertEqual("", user_n.mail_routing_address)
        self.assertNotEqual("", user_n.mail_del_date)  # TODO: Make a more reliable test

# TODO: Test WebmailView

class RedirectMailResElViewCase(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)

        # Fake mailPerson
        mv = MailResEl()
        h = mv.build_address(self.user.uid, self.user.first_name, self.user.last_name)
        self.user.mail_local_address = h + '@resel.fr'
        self.user.mail_dir = self.user.uid + '/Maildir/'
        self.user.mail_del_date = None
        self.user.home_directory = '/var/mail/virtual/' + self.user.uid
        self.user.object_classes = ['mailPerson']
        self.user.save()

        self.client.login(username=self.user.uid, password=self.user.user_password)

    def test_create_redirection(self):
        new_address = "bernard.lowe@westworld.us"

        r = self.client.get(reverse("gestion-personnes:redirect-mail"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/mail_redirect.html")

        r = self.client.post(reverse("gestion-personnes:redirect-mail"),
                                data={"new_routing_address": new_address},
                                HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)

        user_mod = LdapUser.get(uid=self.user.uid)
        self.assertEqual(user_mod.mail_routing_address, new_address)

    def test_delete_redirection(self):
        r = self.client.get(reverse("gestion-personnes:redirect-mail"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "gestion_personnes/mail_redirect.html")

        r = self.client.post(reverse("gestion-personnes:redirect-mail"),
                                data={"new_routing_address": ""},
                                HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)

        user_mod = LdapUser.get(uid=self.user.uid)
        self.assertEqual(user_mod.mail_routing_address, "")
