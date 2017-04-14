from django.test import TestCase

from django.core.urlresolvers import reverse

from gestion_personnes.tests import create_full_user, try_delete_user
from gestion_personnes.models import LdapUser

# Create your tests here.

class HomeTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="penis")
        user.save()

        self.client.login(username="jbvallad", password="penis")

    def testSimpleLoad(self):
        r = self.client.get(reverse("campus:who:user-home"),
                                   HTTP_HOST="10.0.3.99")
        self.assertEqual(200, r.status_code)

    def testEditUserInfo(self):
        user = LdapUser.get(pk="jbvallad")
        r = self.client.post(
            reverse("campus:who:user-home"),
            data={
                'email' : user.mail,
                'campus' : user.campus,
                'building' : user.building,
                'room' : user.room_number,
                'address' : user.postal_address,
                'birth_date' : user.birth_date,
                'is_public' : user.is_public,
            },
            HTTP_HOST="10.0.3.99",
            follow = True
        )

        self.assertEqual(200, r.status_code)

class SearchTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="penis")
        user.save()

        self.client.login(username="jbvallad", password="penis")

    def testSimpleLoad(self):
        r = self.client.post(
            reverse("campus:who:search-user"),
            data={
                'what': "Alexandre",
                'is_approx': False
            },
            HTTP_HOST="10.0.3.99",
            follow = True
        )
        self.assertEqual(200, r.status_code)

class UserDetailTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="penis")
        user.save()

        self.client.login(username="jbvallad", password="penis")

    def testSimpleLoad(self):
        user = LdapUser.get(pk="jbvallad")
        r = self.client.get(
            reverse("campus:who:user-details", kwargs={'uid': user.uid} ),
            HTTP_HOST="10.0.3.99",
            follow = True
        )
        self.assertEqual(200, r.status_code)

        r2 = self.client.get(
            reverse("campus:who:user-details", kwargs={'uid': "tfwIDoNotExist"} ),
            HTTP_HOST="10.0.3.99",
            follow = True
        )
        self.assertEqual(404, r2.status_code)
