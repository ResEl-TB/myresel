# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from gestion_machines.models import LdapDevice


class LdapDeviceTestCase(TestCase):
    def new_dummy_activated_device(self):
        device = LdapDevice()

        device.hostname = "mymachine"
        device.set_owner("lcarr")
        device.ip = "120.45"
        device.activate("Brest")

    @staticmethod
    def try_delete_device(pk):
        try:
            device_s = LdapDevice.get(pk=pk)
            device_s.delete()
            return True
        except ObjectDoesNotExist:
            return False

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

    def test_simple_device_save(self):
        self.try_delete_device("testsimpledevicelcarr")

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
        self.try_delete_device("testdevicelcarr")

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

    # TODO: test multiple same mac devices
    # TODO: test invalid mac or ip
    # TODO: test multiple same hostname
