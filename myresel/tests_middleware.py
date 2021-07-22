# -*- coding: utf-8 -*-
"""
Test the default myresel middleware

Inspired by: http://blog.namis.me/2012/05/13/writing-unit-tests-for-django-middleware/
"""
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from gestion_personnes.tests import try_delete_user, create_full_user
from myresel import middleware
from fonctions import ldap

class AdminMiddlewareTestCase(TestCase):

    def setUp(self):
        self.cm = middleware.IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAResElAdminSoCheckTheLdapBeforeMiddleware(lambda x:None)
        self.request = Mock()
        self.request.session = {}
        self.request.user.username = ""
        self.request.user.is_staff = 0
        self.request.user.is_superuser = 0

        # Create an admin user
        try_delete_user("lcarr")
        self.admin_user = create_full_user(uid="lcarr")
        self.admin_user.save()
        self.admin_dn = ldap.create_admin(uid="lcarr")
        self.admin_uid = "lcarr"
        self.admin_pwd = "blahblah"
        admin = User(username="lcarr")
        admin.save()

        try_delete_user("amanoury")
        self.user = create_full_user(uid="amanoury")
        self.user.save()

    def test_user_is_admin(self):
        self.request.user.username = self.admin_uid

        self.assertEqual(self.cm(self.request), None)
        self.request.user = User.objects.get(username=self.request.user.username)
        self.assertEqual(self.request.user.is_staff, 1)
        self.assertEqual(self.request.user.is_superuser, 1)

    def test_user_is_not_admin(self):
        self.request.user.username = self.user.uid

        self.assertEqual(self.cm(self.request), None)
        self.assertEqual(self.request.user.is_staff, 0)
        self.assertEqual(self.request.user.is_superuser, 0)

    def test_full_request_admin(self):
        self.client.login(username="lcarr", password="blahblah")
        self.client.get(reverse("home"),
                        HTTP_HOST="10.0.3.94", follow=True)
        # Double request because it is not instant
        r = self.client.get(reverse("home"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertContains(r, 'href="/gestion"')


    def test_full_request_not_admin(self):
        self.client.login(username="amanoury", password="blahblah")
        r = self.client.get(reverse("home"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEquals(200, r.status_code)
        self.assertNotContains(r, 'href="/gestion"')
