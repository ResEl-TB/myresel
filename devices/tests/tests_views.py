# -*- coding: utf-8 -*-
"""
Test the views of the device management module
"""
import json
from unittest import skip

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from devices.models import LdapDevice
from devices.tests.tests import try_delete_device
from gestion_personnes.tests import try_delete_user, try_delete_old_user, create_full_user
from myresel import settings


class ManualAddCase(TestCase):
    owner = ("uid=amanoury,%s" % settings.LDAP_DN_PEOPLE)
    invalid_macs = ['dsfsdf', "0z:12:23:34:45:56", "12:23:34:45:56"]  # TODO: add : 00:00:00:00:00:00, ff:ff:ff:ff:ff:ff if necessary...
    valid_macs = ['01:12:23:34:45:56', "0a:00:27:00:00:05", "0a-00-27-00-00-03", "0A:0D:27:00:00:03", "0A-0D-27-00-00-03"]

    def setUp(self):
        try_delete_user("amanoury")
        try_delete_old_user("amanoury")
        self.user = create_full_user()
        self.user.save()

        self.client.login(username=self.user.uid, password=self.user.user_password)
        user_devices = LdapDevice.filter(owner=self.owner)
        for mac in self.invalid_macs + self.valid_macs:
            user_devices += LdapDevice.filter(mac_address=mac)

        for device in user_devices:
            device.delete()

    def test_simple_add(self):
        r = self.client.get(reverse("gestion-machines:ajout-manuel"),
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "devices/manual_add_device.html")

        r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                    {'mac': '01:12:23:34:45:56',
                                     'description': "fake description"},
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'devices/list_devices.html')
        self.assertContains(r, "Votre demande a")
        self.assertEqual(1, len(mail.outbox))

    def test_double_add(self):
        # Creating ldap form
        device = LdapDevice()
        device.hostname = "pcamanoury012"
        device.set_owner(self.owner)
        device.ip = "200.222"
        device.mac_address = '01:12:23:34:45:56'
        device.zones = ["Brest", "User"]
        device.save()

        r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                             {'mac': '01:12:23:34:45:56'},
                             ZONE="Brest-any", HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'devices/manual_add_device.html')
        self.assertContains(r, "Cette machine est")
        self.assertEqual(1, len(mail.outbox))

    def test_invalid_mac(self):
        for mac in self.invalid_macs:
            r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                 {'mac': mac, 'description': "fake description"},
                                 ZONE="Brest-any", HTTP_HOST="10.0.3.99", follow=True)
            self.assertEqual(200, r.status_code)
            self.assertTemplateUsed(r, 'devices/manual_add_device.html')
            self.assertContains(r, "Adresse MAC non valide")

    def test_valid_macs(self):
        for mac in self.valid_macs:
            r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                 {'mac': mac, 'description': "fake description"},
                                 ZONE="Brest-any", HTTP_HOST="10.0.3.99", follow=True)

            self.assertEqual(200, r.status_code)
            self.assertTemplateUsed(r, 'devices/list_devices.html')
            self.assertContains(r, "Votre demande a")

    def test_invalid_description(self):
        r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                    {'mac': '01:12:23:34:45:56'},
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'devices/manual_add_device.html')
        self.assertContains(r, "Ce champ est obligatoire.")


class ListDevicesCase(TestCase):
    pass  # TODO


class EditDeviceCase(TestCase):
    pass  # TODO
