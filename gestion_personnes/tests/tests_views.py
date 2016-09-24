# -*- coding: utf-8 -*-
"""
Test the views in the current module
"""
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.test import TestCase

from fonctions.generic import hash_to_ntpass
from gestion_machines.models import LdapDevice
from gestion_personnes.models import LdapUser
from gestion_personnes.tests import try_delete_user, create_full_user
from myresel import settings


def try_delete_device(mac):
    try:
        device_s = LdapDevice.get(mac_address=mac)
        device_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


class InscriptionCase(TestCase):
    def setUp(self):
        try_delete_user("lcarr")
        try_delete_device(settings.DEBUG_SETTINGS['mac'])

    def test_simple(self):
        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.199")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

    def test_full_signup(self):
        user = create_full_user()
        try_delete_user(user.uid)

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_personnes/inscription.html")

        r = self.client.post(reverse(
            "gestion-personnes:inscription"),
            data={
                'last_name': user.last_name,
                'first_name': user.first_name,
                'formation': user.formation,
                'email': user.mail,
                'password': user.user_password,
                'password_verification': user.user_password,
                'campus': user.campus,
                'building': user.building,
                'room': user.room_number,
                'phone': user.mobile,
                'certify_truth': 'certify_truth',
            },
            HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/cgu.html')

        r = self.client.post(
            reverse("gestion-personnes:cgu"),
            data={
                'have_read': 'have_read'
            },
            HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'gestion_personnes/finalize_signup.html')
        self.assertContains(r, user.uid)

        user_s = LdapUser.get(pk=user.uid)
        self.assertEqual(user.uid, user_s.uid)
        self.assertEqual(user.first_name, user_s.first_name)
        self.assertEqual(user.last_name, user_s.last_name)
        self.assertEqual(user.building, user_s.building)
        self.assertEqual(user.campus, user_s.campus)

        # TODO: find a way to check if emails are sent...
        # get_worker().work(burst=True)
        # self.assertEqual(3, len(mail.outbox))

    def test_simple_wrong_network(self):
        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "pages/home/home.html")

    def test_already_known_device(self):
        user = LdapUser()
        user.uid = 'lcarr'
        user.first_name = "Loïc"
        user.last_name = "Carr"
        user.user_password = "blah"
        user.nt_password = user.user_password
        user.save()

        device = LdapDevice()
        device.hostname = "testhostname243"
        device.owner = user.pk
        device.ip = "42.42"
        device.mac_address = settings.DEBUG_SETTINGS['mac']
        device.activate("Brest")
        device.save()

        response = self.client.get(reverse("gestion-personnes:inscription"),
                                   HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "pages/inscription_zone_info.html")

        response2 = self.client.get(reverse("gestion-personnes:inscription"),
                                    HTTP_HOST="10.0.3.199", follow=True)
        self.assertEqual(200, response2.status_code)
        self.assertTemplateUsed(response2, "pages/inscription_zone_info.html")


class ModPasswdCase(TestCase):
    def setUp(self):
        try_delete_user("lcarr")
        try_delete_device(settings.DEBUG_SETTINGS['mac'])

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
        self.assertEqual(hash_to_ntpass("blohhhhhhh"), u.nt_password)
        # self.assertEqual(hash_passwd("blohhhhhhh"), u.user_password)

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
        self.assertEqual(hash_to_ntpass("blah"), u.nt_password)
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
        self.assertEqual(hash_to_ntpass("blah"), u.nt_password)
        # self.assertEqual(hash_passwd("blah"), u.user_password)