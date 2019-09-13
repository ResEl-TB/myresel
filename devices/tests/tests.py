# -*- coding: utf-8 -*-
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from devices.forms import ManualDeviceAddForm
from devices.models import LdapDevice


def new_dummy_device(owner="lcarr", auth_type='802.1X', mac="0000000000"):
    device = LdapDevice()

    device.set_owner(owner)
    device.mac_address = mac
    device.auth_type = auth_type
    return device


def try_delete_device(mac):
    """
    Try to delete a device

    :param pk: pk of the device to delete
    :return: True if the device was indeed deleted, False otherwise
    """
    try:
        device_s = LdapDevice.get(macAddress=mac)
        device_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


class LdapDeviceTestCase(TestCase):
    def test_set_owner(self):
        device = LdapDevice()
        device.set_owner("camme")

        self.assertEqual("uid=camme,ou=people,dc=maisel,dc=enst-bretagne,dc=fr", device.owner)

    def test_device_save(self):
        try_delete_device("testsimpledevicelcarr")

        device = LdapDevice()
        device.set_owner("lcarr")
        device.mac_address = "122334455667"
        device.auth_type = "802.1X"

        device.save()

        device_s = LdapDevice.get(pk=device.hostname)
        self.assertIsInstance(device_s, LdapDevice)
        self.assertEqual(device.owner, device_s.owner)
        self.assertEqual(device.mac_address, device_s.mac_address)
        self.assertEqual(device.auth_type, device_s.auth_type)


class AjoutManuelFormTestCase(TestCase):
    def setUp(self):
        self.device = new_dummy_device(mac="00:00:00:00:01:00")
        try_delete_device(self.device.mac_address)
        self.device.save()

    def test_simple(self):
        form_data = {
            'mac': '00:00:02:00:01:00',
            'description': "Je fais quoi de ma vie ?"
        }

        form = ManualDeviceAddForm(data=form_data)
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
            form = ManualDeviceAddForm(data=form_data)
            self.assertFalse(form.is_valid())

    def test_notify_existing_mac(self):
        form_data = {
            'mac': self.device.mac_address,
            'description': "Je fais quoi de ma vie ?"
        }

        form = ManualDeviceAddForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(mail.outbox), 1)
