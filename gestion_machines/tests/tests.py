# -*- coding: utf-8 -*-
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from gestion_machines.forms import AjoutManuelForm
from gestion_machines.models import LdapDevice


def new_dummy_device(owner="lcarr", hostname="mymachine", activated=True, ip="120.45", mac="00:00:00:00:00"):
    device = LdapDevice()

    device.hostname = hostname
    device.set_owner(owner)
    device.ip = ip
    device.mac_address = mac
    if activated:
        device.activate("Brest")
    return device


def try_delete_device(pk):
    """
    Try to delete a device

    :param pk: pk of the device to delete
    :return: True if the device was indeed deleted, False otherwise
    """
    try:
        device_s = LdapDevice.get(pk=pk)
        device_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


class LdapDeviceTestCase(TestCase):
    def test_set_owner(self):
        device = LdapDevice()
        device.set_owner("camme")

        self.assertEqual("uid=camme,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", device.owner)

    def test_add_zone(self):
        device = LdapDevice()
        device.add_zone("Paris")

        self.assertEqual(1, len(device.zones))
        self.assertIn("Paris", device.zones)

        device.add_zone("Lille")
        self.assertEqual(2, len(device.zones))
        self.assertIn("Lille", device.zones)

        device.add_zone("Lille")  # Check if the zone is not added twice
        self.assertEqual(2, len(device.zones))
        self.assertIn("Lille", device.zones)

    def test_set_campus(self):
        device = LdapDevice()
        device.set_campus("Brest")
        self.assertEqual("Brest", device.get_campus())

        device.set_campus("Rennes")
        self.assertEqual("Rennes", device.get_campus())

        with self.assertRaises(ValueError):
            device.set_campus("Paris")
            # self.assertEqual("Rennes", device.get_campus())

    def test_activate(self):
        device = LdapDevice()
        device.activate("Brest")

        self.assertEqual("active", device.get_status())
        self.assertEqual("Brest", device.get_campus())

        device.activate("Rennes")
        self.assertEqual("Rennes", device.get_campus())
        self.assertEqual("wrong_campus", device.get_status())

    def test_is_inactive(self):
        device = LdapDevice()
        device.activate("Brest")

        self.assertFalse(device.is_inactive())

        device.replace_or_add_zone("User", "Inactive")

        self.assertTrue(device.is_inactive())

    def test_simple_device_save(self):
        try_delete_device("testsimpledevicelcarr")

        device = LdapDevice()
        device.hostname = "testsimpledevicelcarr"
        device.set_owner("lcarr")
        device.ip = "123.213"
        device.zones = ["Brest", "User"]
        device.mac_address = "12:23:34:45:56:67"

        device.save()

        device_s = LdapDevice.get(pk=device.hostname)
        self.assertIsInstance(device_s, LdapDevice)
        self.assertEqual(device.hostname, device_s.hostname)
        self.assertEqual(device.ip, device_s.ip)
        self.assertEqual(device.owner, device_s.owner)
        self.assertEqual(device.mac_address, device_s.mac_address)

    def test_device_save(self):
        try_delete_device("testdevicelcarr")

        device = LdapDevice()
        device.hostname = "testdevicelcarr"
        device.set_owner("lcarr")
        device.ip = "123.213"
        device.mac_address = "12:23:34:45:56:67"
        device.activate("Brest")

        device.save()

        device_s = LdapDevice.get(pk=device.hostname)
        self.assertIsInstance(device_s, LdapDevice)
        self.assertEqual(device.hostname, device_s.hostname)
        self.assertEqual(device.ip, device_s.ip)
        self.assertEqual(device.owner, device_s.owner)

    def test_device_save_empty_mac(self):
        try_delete_device("emptydevicelcarr")

        device = LdapDevice()
        device.hostname = "emptydevicelcarr"
        device.set_owner("lcarr")
        device.ip = "123.213"
        device.mac_address = ""
        device.activate("Brest")

        with self.assertRaises(ValueError):
            device.save()

    def test_replace_or_add_zone(self):
        device1 = LdapDevice()
        device1.zones = ['User']
        device1.replace_or_add_zone("Home", "Cat")

        self.assertListEqual(['User', 'Cat'], device1.zones)

        device2 = LdapDevice()
        device2.zones = ['User']
        device2.replace_or_add_zone('User', 'Cat')

        self.assertListEqual(['Cat'], device2.zones)

        device3 = LdapDevice()
        device3.zones = ['User', 'Home']
        device3.replace_or_add_zone('User', 'Home')

        self.assertListEqual(['Home'], device3.zones)

    # TODO: test multiple same mac devices
    # TODO: test invalid mac or ip
    # TODO: test multiple same hostname


class AjoutManuelFormTestCase(TestCase):
    def setUp(self):
        self.device = new_dummy_device(mac="00:00:00:00:01:00")
        try_delete_device(self.device.hostname)
        self.device.save()

    def test_simple(self):
        form_data = {
            'mac': '00:00:02:00:01:00',
            'description': "Je fais quoi de ma vie ?"
        }

        form = AjoutManuelForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_data(self):
        inputs = [{
            'mac': '00:00:0200:01:00',
            'description': "Je fais quoi de ma vie ?"
            },
            {
                'mac': '00:00:03:00:01:00',
                'description': "",
            },
        ]
        for form_data in inputs:
            form = AjoutManuelForm(data=form_data)
            self.assertFalse(form.is_valid())

    def test_notify_existing_mac(self):
        form_data = {
            'mac': self.device.mac_address,
            'description': "Je fais quoi de ma vie ?"
        }

        form = AjoutManuelForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(mail.outbox), 1)