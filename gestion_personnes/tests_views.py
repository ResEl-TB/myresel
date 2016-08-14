# -*- coding: utf-8 -*-
"""
Test the views in the current module
"""
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.test import TestCase

from gestion_machines.models import LdapDevice
from gestion_personnes.models import LdapUser
from gestion_personnes.tests import try_delete_user
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

