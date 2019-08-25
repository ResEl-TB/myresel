# -*- coding: utf-8 -*-

from django.test import TestCase
from myresel import settings

from fonctions.generic import hash_passwd, compare_passwd
from fonctions.network import update_all, NetworkError


class FunctionTests(TestCase):
    def setUp(self):
        pass

    def test_passwd_compare(self):
        h = hash_passwd("blah")

        self.assertTrue(compare_passwd("blah", h))
        self.assertFalse(compare_passwd("blohs", h))

    def test_update_all(self):
        # Simply test if the command launch with no error
        update_all()

    def create_redis_conn(self):
        import redis
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB
        )
