# -*- coding: utf-8 -*-

from django.test import TestCase
from myresel import settings

from fonctions.generic import hash_passwd, compare_passwd
from fonctions.network import get_network_zone, is_resel_ip, update_all, get_campus, NetworkError


class FunctionTests(TestCase):
    def setUp(self):
        pass

    def test_passwd_compare(self):
        h = hash_passwd("blah")

        self.assertTrue(compare_passwd("blah", h))
        self.assertFalse(compare_passwd("blohs", h))

    def test_is_resel_ip(self):
        self.assertTrue(is_resel_ip("172.22.2.123"))
        self.assertTrue(is_resel_ip("172.22.220.214"))
        self.assertTrue(is_resel_ip("172.23.0.1"))

        self.assertFalse(is_resel_ip("8.8.8.8"))
        self.assertFalse(is_resel_ip("172.25.21.123"))
        self.assertFalse(is_resel_ip("172.22.21.321"))  # This is not an ip

    def test_update_all(self):
        # Simply test if the command launch with no error
        update_all()

    def test_get_campus(self):

        self.assertEqual("Brest", get_campus("172.22.2.123"))
        self.assertEqual("Brest", get_campus("172.22.200.123"))
        self.assertEqual("Brest", get_campus("172.22.42.123"))

        self.assertEqual("Rennes", get_campus("172.23.2.123"))
        self.assertEqual("Rennes", get_campus("172.23.200.123"))
        self.assertEqual("Rennes", get_campus("172.23.42.123"))

        self.assertRaises(NetworkError, get_campus, "8.8.8.8")
        self.assertRaises(NetworkError, get_campus, "168.234.164.134")
        self.assertRaises(NetworkError, get_campus, "172.22.412.312")
        self.assertRaises(NetworkError, get_campus, "200.123")
        self.assertRaises(NetworkError, get_campus, "172.22.123.200.123")

    def create_redis_conn(self):
        import redis
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB
        )
