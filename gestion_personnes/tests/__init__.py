# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from gestion_personnes.models import LdapUser, LdapOldUser


def try_delete_user(uid):
    try:
        user_s = LdapUser.get(pk=uid)
        user_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


def try_delete_old_user(uid):
    try:
        user_s = LdapOldUser.get(pk=uid)
        user_s.delete()
        return True
    except ObjectDoesNotExist:
        return False


def create_full_user():
    now = datetime.now()
    now = now.replace(microsecond=0)
    user = LdapUser()
    user.uid = "amanoury"
    user.first_name = "Alexandre"
    user.last_name = "Manoury"
    user.user_password = "blahblah"
    user.nt_password = "blahblah"
    user.display_name = "Alexandre Manoury"
    user.postal_address = "I11 Maisel blah\n blah blah"

    user.inscr_date = now
    user.cotiz = "2016"
    user.end_cotiz = now
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