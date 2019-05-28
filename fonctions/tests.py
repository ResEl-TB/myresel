# -*- coding: utf-8 -*-

from django.test import TestCase
from myresel import settings

from fonctions.generic import hash_passwd, compare_passwd
from fonctions.network import get_network_zone, is_resel_ip, update_all, get_campus, NetworkError, get_mac


class FunctionTests(TestCase):
    def setUp(self):
        pass

    def test_passwd_compare(self):
        h = hash_passwd("blah")

        self.assertTrue(compare_passwd("blah", h))
        self.assertFalse(compare_passwd("blohs", h))

    def test_get_network_zone(self):
        # Oui, je me suis fait chier à tout taper :/

        self.assertEqual("Brest-inscription", get_network_zone("172.22.224.1"))
        self.assertEqual("Brest-inscription", get_network_zone("172.22.224.254"))
        self.assertEqual("Brest-inscription", get_network_zone("172.22.225.3"))
        self.assertEqual("Brest-inscription", get_network_zone("172.22.225.234"))

        self.assertEqual("Brest-inscription-999", get_network_zone("172.22.226.1"))
        self.assertEqual("Brest-inscription-999", get_network_zone("172.22.226.254"))
        self.assertEqual("Brest-inscription-999", get_network_zone("172.22.227.23"))
        self.assertEqual("Brest-inscription-999", get_network_zone("172.22.227.234"))

        self.assertEqual("Brest-user", get_network_zone("172.22.200.1"))
        self.assertEqual("Brest-user", get_network_zone("172.22.200.1"))
        self.assertEqual("Brest-user", get_network_zone("172.22.210.54"))
        self.assertEqual("Brest-user", get_network_zone("172.22.222.234"))
        self.assertEqual("Brest-user", get_network_zone("172.22.223.234"))

        self.assertEqual("Brest-other", get_network_zone("172.22.2.234"))
        self.assertEqual("Brest-other", get_network_zone("172.22.0.123"))
        self.assertEqual("Brest-other", get_network_zone("172.22.42.142"))


        self.assertEqual("Rennes-inscription", get_network_zone("172.23.224.1"))
        self.assertEqual("Rennes-inscription", get_network_zone("172.23.224.254"))
        self.assertEqual("Rennes-inscription", get_network_zone("172.23.225.3"))
        self.assertEqual("Rennes-inscription", get_network_zone("172.23.225.234"))

        self.assertEqual("Rennes-inscription-999", get_network_zone("172.23.226.1"))
        self.assertEqual("Rennes-inscription-999", get_network_zone("172.23.226.254"))
        self.assertEqual("Rennes-inscription-999", get_network_zone("172.23.227.23"))
        self.assertEqual("Rennes-inscription-999", get_network_zone("172.23.227.234"))

        self.assertEqual("Rennes-user", get_network_zone("172.23.200.1"))
        self.assertEqual("Rennes-user", get_network_zone("172.23.200.1"))
        self.assertEqual("Rennes-user", get_network_zone("172.23.210.54"))
        self.assertEqual("Rennes-user", get_network_zone("172.23.222.234"))
        self.assertEqual("Rennes-user", get_network_zone("172.23.223.234"))

        self.assertEqual("Rennes-other", get_network_zone("172.23.2.234"))
        self.assertEqual("Rennes-other", get_network_zone("172.23.0.123"))
        self.assertEqual("Rennes-other", get_network_zone("172.23.42.142"))

        self.assertEqual("Internet", get_network_zone("8.8.8.8"))
        self.assertEqual("Internet", get_network_zone("123.142.253.174"))
        self.assertRaises(NetworkError, get_network_zone, ip_str="168.2.324.197")

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

    def test_get_mac_ip(self):
        # Create fake adresses:
        r = self.create_redis_conn()
        r.set('mac__172.22.200.123', '34:64:4c:ab:22:96')
        r.set('mac__172.23.200.100', '35:ac:80:a4:12:00')

        # Commented since Redis disabled
        #self.assertEqual('34:64:4c:ab:22:96', get_mac('172.22.200.123'))
        #self.assertEqual('35:ac:80:a4:12:00', get_mac('172.23.200.100'))

    def test_get_mac_ip_no_redis(self):
        r = self.create_redis_conn()
        r.delete('mac__172.22.200.123', '34:64:4c:ab:22:96')
        r.delete('mac__172.23.200.100', '35:ac:80:a4:12:00')

        self.assertEqual(settings.DEBUG_SETTINGS['mac'], get_mac('172.22.209.115'))
