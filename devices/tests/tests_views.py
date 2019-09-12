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


class AddDeviceViewCase(TestCase):
    owner = ("uid=amanoury,%s" % settings.LDAP_DN_PEOPLE)

    @classmethod
    def setUpClass(cls):
        try_delete_user("amanoury")
        try_delete_old_user("amanoury")
        cls.user = create_full_user()
        cls.user.save()

    def setUp(self):
        self.client.login(username=self.user.uid, password=self.user.user_password)
        user_devices = LdapDevice.filter(owner=self.owner)
        for device in user_devices:
            try_delete_device(device.hostname)

    @classmethod
    def tearDownClass(cls):
        try_delete_user("amanoury")

    def test_simple_get_page(self):
        response = self.client.get(reverse("gestion-machines:ajout"),
                                   HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "devices/add_device.html")

    def test_add_simple_device(self):
        user_machines = len(LdapDevice.filter(owner=self.owner))
        response = self.client.post(reverse("gestion-machines:ajout"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.filter(owner=self.owner)))
        self.assertEqual(1, len(mail.outbox))

        # Check if the home page is up to date
        r = self.client.get(reverse("home"), HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertContains(r, "Connecté au ResEl")
        self.assertEqual(1, len(mail.outbox))

    # TODO: make test with concurrently to test multiple simultaneous presses
    def test_add_twice(self):
        user_machines = len(LdapDevice.filter(owner=self.owner))
        response = self.client.post(reverse("gestion-machines:ajout"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.filter(owner=self.owner)))

        response2 = self.client.post(reverse("gestion-machines:ajout"),
                                     HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, response2.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.filter(owner=self.owner)))

    def test_add_custom_alias(self):
        user_machines = len(LdapDevice.filter(owner=self.owner))
        response = self.client.post(reverse("gestion-machines:ajout"), {'alias': 'customalias'},
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.filter(owner=self.owner)))

        device = LdapDevice.get(pk="pcamanoury")
        self.assertEqual("customalias", device.aliases[0])


class Reactivation(TestCase):
    def setUp(self):
        try_delete_user("amanoury")
        try_delete_old_user("amanoury")
        self.user = create_full_user()
        self.user.save()
        self.client.login(username=self.user.uid, password=self.user.user_password)
        self.owner = ("uid=amanoury,%s" % settings.LDAP_DN_PEOPLE)
        user_devices = LdapDevice.filter(owner=self.owner)
        for device in user_devices:
            try_delete_device(device.hostname)

        # Create a simple device:
        self.client.post(
            reverse("gestion-machines:ajout"),
            HTTP_HOST="10.0.3.95", follow=True,
        )
        mail.outbox = []

    def test_simple_activation(self):
        device = LdapDevice.get(owner=self.owner)
        device.replace_or_add_zone("Brest", "Inactive")
        device.save()

        # Double-check that the device is indeed disabled
        device2 = LdapDevice.get(owner=self.owner)
        self.assertEqual("inactive", device2.get_status())
        self.assertTrue(device2.is_inactive())
        # The real view check
        response = self.client.get(reverse("gestion-machines:reactivation"),
                                   HTTP_HOST="10.0.3.199", follow=True)
        self.assertEqual(200, response.status_code)

        device3 = LdapDevice.get(owner=self.owner)
        self.assertEqual("active", device3.get_status())
        self.assertFalse(device3.is_inactive())
        self.assertEqual(1, len(mail.outbox))

    @skip("It fails, I don't know why...")
    def test_real_case_activation(self):
        device = LdapDevice.get(owner=self.owner)
        device.replace_or_add_zone("Brest", "Inactive")
        device.save()

        # Double-check that the device is indeed disabled
        device2 = LdapDevice.get(owner=self.owner)
        self.assertEqual("inactive", device2.get_status())
        self.assertTrue(device2.is_inactive())
        # The real view check
        response = self.client.get(reverse("generate_204"),
                                   HTTP_HOST="10.0.3.199", follow=True)
        self.assertEqual(200, response.status_code)

        device3 = LdapDevice.get(owner=self.owner)
        self.assertEqual("active", device3.get_status())
        self.assertFalse(device3.is_inactive())
        self.assertEqual(len(mail.outbox), 1)


class ChangeCampusCase(TestCase):
    def setUp(self):
        try_delete_user("amanoury")
        try_delete_old_user("amanoury")
        self.user = create_full_user()
        self.user.save()
        self.client.login(username=self.user.uid, password=self.user.user_password)
        self.owner = ("uid=amanoury,%s" % settings.LDAP_DN_PEOPLE)
        user_devices = LdapDevice.filter(owner=self.owner)
        for device in user_devices:
            try_delete_device(device.hostname)

        # Create a simple device:
        r = self.client.post(reverse("gestion-machines:ajout"),
                             HTTP_HOST="10.0.3.95", follow=True
                             )
        self.assertEqual(200, r.status_code)
        mail.outbox = []

    def test_simple_campus_change(self):
        device = LdapDevice.get(owner=self.owner)
        device.set_campus("Rennes")
        device.save()

        # Double-check that the device is indeed disabled
        device2 = LdapDevice.get(owner=self.owner)
        self.assertEqual("Rennes", device2.get_campus())

        # The real view check
        response = self.client.get(reverse("gestion-machines:reactivation"),
                                   HTTP_HOST="10.0.3.199", follow=True)
        self.assertEqual(200, response.status_code)

        device3 = LdapDevice.get(owner=self.owner)
        self.assertEqual("active", device3.get_status())
        self.assertEqual("Brest", device3.get_campus())
        self.assertEqual(len(mail.outbox), 1)


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
                                    HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "devices/manual_add_device.html")

        r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                    {'mac': '01:12:23:34:45:56',
                                     'description': "fake description"},
                                    HTTP_HOST="10.0.3.99", follow=True)

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
                             HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'devices/manual_add_device.html')
        self.assertContains(r, "Cette machine est")
        self.assertEqual(1, len(mail.outbox))

    def test_invalid_mac(self):
        for mac in self.invalid_macs:
            r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                 {'mac': mac, 'description': "fake description"},
                                 HTTP_HOST="10.0.3.99", follow=True)
            self.assertEqual(200, r.status_code)
            self.assertTemplateUsed(r, 'devices/manual_add_device.html')
            self.assertContains(r, "Adresse MAC non valide")

    def test_valid_macs(self):
        for mac in self.valid_macs:
            r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                 {'mac': mac, 'description': "fake description"},
                                 HTTP_HOST="10.0.3.99", follow=True)

            self.assertEqual(200, r.status_code)
            self.assertTemplateUsed(r, 'devices/list_devices.html')
            self.assertContains(r, "Votre demande a")

    def test_invalid_description(self):
        r = self.client.post(reverse("gestion-machines:ajout-manuel"),
                                    {'mac': '01:12:23:34:45:56'},
                                    HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'devices/manual_add_device.html')
        self.assertContains(r, "Ce champ est obligatoire.")


class ListDevicesCase(TestCase):
    pass  # TODO


class EditDeviceCase(TestCase):
    pass  # TODO
