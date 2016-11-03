# -*- coding: utf-8 -*-

from django.test import TestCase

from fonctions.generic import hash_passwd, compare_passwd


class FunctionTests(TestCase):
    def setUp(self):
        pass

    def test_passwd_compare(self):
        h = hash_passwd("blah")

        self.assertTrue(compare_passwd("blah", h))
        self.assertFalse(compare_passwd("blohs", h))