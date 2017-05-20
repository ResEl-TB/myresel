# -*- coding: utf-8 -*-
from unittest import skip

from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse

from gestion_personnes.models import LdapUser
from gestion_personnes.tests import try_delete_user


class CreateCampusMail(TestCase):
    def setUp(self):
        try_delete_user("lcarr")

        user = LdapUser()
        user.uid = 'lcarr'
        user.first_name = "Loïc"
        user.last_name = "Carr"
        user.user_password = "blah"
        user.mail = "loic.carr@resel.fr"
        user.promo = 2016
        user.nt_password = user.user_password
        user.save()

        self.client.login(username="lcarr", password="blah")

    def test_load_create_simple_email(self):
        r = self.client.get(reverse("campus:mails:send"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)

    @skip("View not ready, crsf error")  # TODO: don't forget to reactivate the test
    def test_create_simple_email(self):
        r = self.client.get(reverse("campus:mails:send"),
                        HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "campus/mails/send_mail.html")

        r = self.client.post(
            reverse("campus:mails:send"),
            HTTP_HOST="10.0.3.99", follow=True,
            data={
                "sender": "loic.carr@resel.fr",
                "subject": "fuu",
                "content": "Wheyudsf  dsqj dsq LOREM IPSUM",
            })

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertEqual(2, len(mail.outbox))
