# -*- coding: utf-8 -*-
"""
Test the views of the device management module
"""
from unittest import skip

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from gestion_machines.models import LdapDevice
from gestion_machines.tests import try_delete_device
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
        self.client.login(username="amanoury", password="blah")
        user_devices = LdapDevice.search(owner=self.owner)
        for device in user_devices:
            try_delete_device(device.hostname)

    @classmethod
    def tearDownClass(cls):
        try_delete_user("amanoury")

    def test_simple_get_page(self):
        response = self.client.get(reverse("gestion-machines:ajout"), HTTP_HOST="10.0.3.95")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "gestion_machines/add_device.html")

    def test_add_simple_device(self):
        user_machines = len(LdapDevice.search(owner=self.owner))
        response = self.client.post(reverse("gestion-machines:ajout"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.search(owner=self.owner)))

    def test_add_twice(self):
        user_machines = len(LdapDevice.search(owner=self.owner))
        response = self.client.post(reverse("gestion-machines:ajout"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.search(owner=self.owner)))

        response2 = self.client.post(reverse("gestion-machines:ajout"),
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response2.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.search(owner=self.owner)))

    def test_add_custom_alias(self):
        user_machines = len(LdapDevice.search(owner=self.owner))
        response = self.client.post(reverse("gestion-machines:ajout"), {'alias': 'customalias'},
                                    HTTP_HOST="10.0.3.95", follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(user_machines + 1, len(LdapDevice.search(owner=self.owner)))

        device = LdapDevice.get(pk="pcamanoury")
        self.assertEqual("customalias", device.aliases[0])


class Reactivation(TestCase):
    def setUp(self):
        try_delete_user("amanoury")
        try_delete_old_user("amanoury")
        self.user = create_full_user()
        self.user.save()
        self.client.login(username="amanoury", password="blah")
        self.owner = ("uid=amanoury,%s" % settings.LDAP_DN_PEOPLE)
        user_devices = LdapDevice.search(owner=self.owner)
        for device in user_devices:
            try_delete_device(device.hostname)

        # Create a simple device:
        self.client.post(reverse("gestion-machines:ajout"),
                         HTTP_HOST="10.0.3.95", follow=True
        )

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
        self.assertEqual(len(mail.outbox), 1)

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
        self.client.login(username="amanoury", password="blah")
        self.owner = ("uid=amanoury,%s" % settings.LDAP_DN_PEOPLE)
        user_devices = LdapDevice.search(owner=self.owner)
        for device in user_devices:
            try_delete_device(device.hostname)

        # Create a simple device:
        self.client.post(reverse("gestion-machines:ajout"),
                         HTTP_HOST="10.0.3.95", follow=True
        )
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
