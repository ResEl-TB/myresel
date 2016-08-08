import time

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from gestion_personnes.models import LUser
from ldapback.models.fields import LdapCharField


def try_delete_user(uid):
    try:
        user_s = LUser.get(pk=uid)
        user_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


class LdapuserTestCase(TestCase):
    @staticmethod
    def create_full_user():
        user = LUser()
        user.uid = "amanoury"
        user.first_name = "Alexandre"
        user.last_name = "Manoury"
        user.user_password = "blah"
        user.nt_password = "blah"
        user.display_name = "Alexandre Manoury"
        user.postal_address = "I11 Maisel blah\n blah blah"

        user.inscr_date = time.strftime('%Y%m%d%H%M%S') + 'Z'
        user.cotiz = "2016"
        user.end_cotiz = time.strftime('%Y%m%d%H%M%S') + 'Z'
        user.campus = "Brest"
        user.building = "I11"
        user.room_number = "123"

        user.promo = "2020"
        user.mail = "alexandre.manoury@telecom-bretagne.eu"
        user.anneeScolaire = "2015"
        user.mobile = "33676675525"
        user.option = "Brest"
        user.formation = "FIG"

        user.ae_cotiz = "100"
        user.ae_nature = "liquide"
        user.n_adherent = "1235667"

        return user

    def test_new_user(self):
        user = self.create_full_user()
        try_delete_user(user.uid)
        user.save()

        user_s = LUser.get(pk=user.uid)
        self.assertIsInstance(user_s, LUser)
        self.assertEqual(user_s.uid, "amanoury")
        self.assertEqual(user_s.first_name, "Alexandre")
        self.assertEqual(user_s.last_name, "Manoury")
        self.assertEqual(user_s.display_name, "Alexandre Manoury")
        self.assertEqual(user_s.postal_address, "I11 Maisel blah\n blah blah")
        self.assertEqual(user_s.inscr_date, user.inscr_date)
        self.assertEqual(user_s.cotiz, "2016")
        self.assertEqual(user_s.end_cotiz, user.end_cotiz)
        self.assertEqual(user_s.campus, "Brest")
        self.assertEqual(user_s.building, "I11")
        self.assertEqual(user_s.room_number, "123")
        self.assertEqual(user_s.promo, "2020")
        self.assertEqual(user_s.mail, "alexandre.manoury@telecom-bretagne.eu")
        self.assertEqual(user_s.anneeScolaire, "2015")
        self.assertEqual(user_s.mobile, "33676675525")
        self.assertEqual(user_s.option, "Brest")
        self.assertEqual(user_s.formation, "FIG")
        self.assertEqual(user_s.ae_cotiz, "100")
        self.assertEqual(user_s.ae_nature, "liquide")
        self.assertEqual(user_s.n_adherent, "1235667")

        try_delete_user(user.uid)

    def test_only_ResEl(self):
        user = LUser()
        user.uid = "amanoury"
        user.first_name = "Alexandre"
        user.last_name = "Manoury"
        user.user_password = "blah"
        user.nt_password = "blah"

        user.display_name = "Alexandre Manoury"
        user.postal_address = "I11 Maisel blah\n blah blah"

        user.inscr_date = time.strftime('%Y%m%d%H%M%S') + 'Z'
        user.cotiz = "2016"
        user.end_cotiz = time.strftime('%Y%m%d%H%M%S') + 'Z'

        try_delete_user(user.uid)
        user.save()

        user_s = LUser.get(pk=user.uid)
        self.assertIsInstance(user_s, LUser)
        self.assertEqual(user.uid, user_s.uid)
        self.assertIsInstance(user.building, LdapCharField)

        # Now lets add a maisel field :
        user_s.building = "I11"
        user_s.room_number = "203"
        user_s.save()

        user_t = LUser.get(pk=user.uid)
        self.assertIsInstance(user_t, LUser)
        self.assertEqual(user_t.building, "I11")
        self.assertEqual(user_t.room_number, "203")

