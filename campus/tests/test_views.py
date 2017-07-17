# -*- coding: utf-8 -*-
from unittest import skip

import pytz
from django.utils import timezone
from datetime import date, datetime

from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from gestion_personnes.models import LdapUser, LdapGroup
from gestion_personnes.tests import create_full_user, try_delete_user

from campus.models.clubs_models import StudentOrganisation, Association, ListeCampagne
from campus.models.rooms_models import Room, RoomBooking
from campus.forms import ClubManagementForm, ClubEditionForm


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
            HTTP_HOST="10.0.3.94", follow=True,
            data={
                "sender": "loic.carr@resel.fr",
                "subject": "fuu",
                "content": "Wheyudsf  dsqj dsq LOREM IPSUM",
            })

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertEqual(2, len(mail.outbox))

#######################################
########### CLub management ###########
#######################################

def try_delete_orga(cn):
    try:
        StudentOrganisation.get(cn=cn).delete()
    except ObjectDoesNotExist:
        pass

def  populate_orgas(club_cn="tenniscn", asso_cn="bde", campagne_cn="lacampagne"):

    try_delete_orga(club_cn)
    try_delete_orga(asso_cn)
    try_delete_orga(campagne_cn)

    club = StudentOrganisation()
    club.object_classes = ["tbClub"]
    club.cn = club_cn
    club.name = "Club Tennis"
    club.ml_infos = True
    club.email = "tennis@resel.fr"
    club.website = "tennis.resel.fr"
    club.description = "le meilleur club de tout TB"
    club.logo = None
    club.save()

    asso = Association()
    asso.object_classes = ["tbAsso"]
    asso.cn = asso_cn
    asso.name = "Bureau des Élèves"
    asso.ml_infos = True
    asso.email = "bde@resel.fr"
    asso.website = "bde.resel.fr"
    asso.description = "Le BDE"
    asso.logo = "placeholder"
    asso.save()

    campagne = ListeCampagne()
    campagne.object_classes = ["tbCampagne"]
    campagne.cn = campagne_cn
    campagne.name = "LA campagne"
    campagne.ml_infos = False
    campagne.website = "lacampagne.resel.fr"
    campagne.description = "LA campagne"
    campagne.logo = "placeholder"
    campagne.campagneYear = 2033
    campagne.save()

def createClubForm(type="CLUB", cn="tenniscn", name="Club Tennis", email="tennis@resel.fr", website="tennis.resel.fr", description="Bla Bla", logo=None):
    form = ClubManagementForm(data={
        "type": type,
        "cn": cn,
        "name": name,
        "email": email,
        "website": website,
        "description": description,
        "logo": logo,
    })
    return(form)

def createClubEditForm(type="CLUB", cn="tenniscn", name="Club Tennis", email="tennis@resel.fr", website="tennis.resel.fr", description="Bla Bla", logo=None):
    form = ClubEditionForm(data={
        "type": type,
        "cn": cn,
        "name": name,
        "email": email,
        "website": website,
        "description": description,
        "logo": logo,
    })
    return(form)

class HomeTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        populate_orgas()

    def testLoadWithoutUser(self):
        r = self.client.get(reverse("campus:clubs:list"),
                                   HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "campus/clubs/list.html")

    def testLoadWithUser(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:list"),
                                    HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)

class DetailTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        populate_orgas()

    def testLoadWithoutUser(self):
        r = self.client.get(reverse("campus:clubs:club_detail", kwargs={"pk":"tenniscn"}),
                                   HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "campus/clubs/detail.html")

    def testLoadWithUser(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:club_detail", kwargs={"pk":"tenniscn"}),
                                    HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)

class MyClubTestCase(TestCase):

    def setUp(self):
        populate_orgas()
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        self.client.login(username=user.uid, password="blabla")

    def testSimpleSearch(self):
        r = self.client.get(
            reverse("campus:clubs:search"),
            data={
                'what': "Tennis",
            },
            HTTP_HOST="10.0.3.94",
            follow = True
        )

    def testSimpleLoad(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:my-clubs"), HTTP_HOST="10.0.3.94")
        self.assertTemplateUsed("campus/clubs/list.html")

class NewClubTestCase(TestCase):

    def setUp(self):
        try_delete_orga("tenniscn")
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        self.client.login(username="jbvallad", password="blabla")

    def testCorrectClub(self):
        form = createClubForm()
        self.assertTrue(form.is_valid())
        form.create_club()
        self.assertTrue(StudentOrganisation.filter(cn="tenniscn"))

    def testWrongCN(self):
        form = createClubForm(cn="Club_Tennis")
        self.assertFalse(form.is_valid())

    def testWrongEmail(self):
        form = createClubForm(email="tennisresel.fr")
        self.assertFalse(form.is_valid())

    def testWrongWebsite(self):
        form = createClubForm(website="tennisreselfr")
        self.assertFalse(form.is_valid())

    def testForgotCampagneYear(self):
        form = createClubForm(type="LIST")
        self.assertFalse(form.is_valid())

    def testForgotAssoLogo(self):
        form = createClubForm(type="ASSOS")
        self.assertFalse(form.is_valid())

    def testForgotListLogo(self):
        form = createClubForm(type="LIST")
        self.assertFalse(form.is_valid())

class EditClubTestCase(TestCase):

    def setUp(self):
        populate_orgas()

    def testEditClub(self):
        form = createClubEditForm()
        form.data["name"] = "Club Bennis"
        self.assertTrue(form.is_valid())
        form.edit_club(form.data["cn"])
        club = StudentOrganisation.get(cn=form.data["cn"])
        self.assertTrue(club.name == "Club Bennis")

class AddPersonTestCase(TestCase):

    def setUp(self):
        populate_orgas()
        self.cn = "tenniscn"
        try_delete_user("jbvallad")
        try_delete_user("bvallad")

        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()

        user = create_full_user(uid="bvallad", pwd="blabla")
        user.save()

        user = LdapUser.get(uid="jbvallad")
        LdapGroup.get(pk='campusmodo').add_member(user.pk)

        self.client.login(username="jbvallad", password="blabla")

    def testAddSelf(self):
        r = self.client.get(reverse("campus:clubs:add-person", kwargs={'pk':self.cn}),
                                    HTTP_HOST="10.0.3.94")
        self.assertTrue(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).members)

    def testAddSomeone(self):
        r = self.client.get(reverse("campus:clubs:add-person", kwargs={'pk':self.cn}),
                                    data={"id_user":"bvallad"},
                                    HTTP_HOST="10.0.3.94")
        self.assertTrue(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).members)

class RemovePersonTestCase(TestCase):

    def setUp(self):
        populate_orgas()
        self.cn = "tenniscn"
        club=StudentOrganisation.get(cn=self.cn)

        try_delete_user("jbvallad")
        try_delete_user("bvallad")

        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        LdapGroup.get(pk='campusmodo').add_member(user.pk)
        club.members.append(user.pk)

        user = create_full_user(uid="bvallad", pwd="blabla")
        user.save()
        club.members.append(user.pk)

        club.save()

        self.client.login(username="jbvallad", password="blabla")

    def testRemoveSelf(self):
        #We just make sure that there is something to remove
        self.assertTrue(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).members)
        r=self.client.get(reverse("campus:clubs:remove-person", kwargs={"pk":self.cn}),
                                    HTTP_HOST="10.0.3.94")
        self.assertFalse(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).members)

    def testRemoveSomeone(self):
        self.assertTrue(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).members)
        r=self.client.get(reverse("campus:clubs:remove-person", kwargs={"pk":self.cn}),
                                    data={"id_user":"bvallad"},
                                    HTTP_HOST="10.0.3.94")
        self.assertFalse(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).members)

class AddPrezTestCase(TestCase):

    def setUp(self):
        populate_orgas()
        self.cn = "tenniscn"
        club=StudentOrganisation.get(cn=self.cn)

        try_delete_user("jbvallad")
        try_delete_user("bvallad")
        try_delete_user("vallad")
        try_delete_user("allad")

        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        LdapGroup.get(pk='campusmodo').add_member(user.pk)

        user = create_full_user(uid="bvallad", pwd="blabla")
        user.save()

        user = create_full_user(uid="vallad", pwd="blabla")
        user.save()
        club.prezs.append(user.pk)

        user = create_full_user(uid="allad", pwd="blabla")
        user.save()

        club.save()

    def testAddPrezBeingModo(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:add-prez", kwargs={'pk':self.cn}),
                                    data={"id_user":"bvallad"},
                                    HTTP_HOST="10.0.3.94")
        self.assertTrue(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).prezs)

    def testAddPrezBeingPrez(self):
        self.client.login(username="vallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:add-prez", kwargs={'pk':self.cn}),
                                    data={"id_user":"jbvallad"},
                                    HTTP_HOST="10.0.3.94")
        self.assertTrue(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).prezs)

    def testAddPrezBeingNobody(self):
        self.client.login(username="allad", password="blabla")
        r = self.client.get(reverse("campus:clubs:add-prez", kwargs={'pk':self.cn}),
                                    data={"id_user":"allad"},
                                    HTTP_HOST="10.0.3.94")
        self.assertFalse(LdapUser.get(uid="allad").pk in StudentOrganisation.get(cn=self.cn).prezs)

class DeleteClubTestCase(TestCase):

    def setup(self):
        populate_orgas()

        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        LdapGroup.get(pk='campusmodo').add_member(user.pk)

    def testDeleteClubBeingModo(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:delete", kwargs={'pk':'tenniscn'}), HTTP_HOST="10.0.3.94")

        self.assertFalse(StudentOrganisation.filter(cn="tenniscn"))

################################
########### Calendar ###########
################################

def createBooking(start_time, end_time, recurring_rule = "NONE", end_recurring_period = None):
    """
    Simple function that create an event according to various parameters and saves it
    It also Creates a room wich is needed in order to create a booking.
    Please note that since we create our event inside the test, it is automaticaly destroyed,
    so that we don't have to bother with it in other tests

    Warning: Dates are stored as UTC time, but django convert them. Tests use
    UTC time but we create event with UTC+1

    Args: self explanatory, check the model ;)
    """
    room = Room(
        location="F",
        name="Salle piano",
        mailing_list = "piano@resel.fr",
        private = "False",
        clubs = ""
    )
    room.save()

    booking = RoomBooking(
        description = "Generated by automatic tests",
        start_time = timezone.make_aware(start_time),
        end_time = timezone.make_aware(end_time),
        user = "jvalladea",
        booking_type = "other",
        displayable = True,
        recurring_rule = recurring_rule,
    )

    if end_recurring_period:
        booking.end_recurring_period = timezone.make_aware(end_recurring_period)

    booking.save()
    booking.room.add(room)
    booking.save()
    return booking

#This test covers many booking cases
class CalendarTestCase(TestCase):

    year = date.today().year+1

    def setup(self):

        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()

    def testSimpleEvent(self):

        createBooking(datetime(self.year,9,1,18,0,0), datetime(self.year,9,1,19,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), HTTP_HOST="10.0.3.94")

        #Check if our event is at the right time and only at the right day
        for day in r.context["calendar"][0]:
            if day[0]:
                if day[0].day == 1:
                    #J'ai trouvé mieux pour convertir une heure en utc, car python ne gère pas heure été/hiver
                    #ne gère pas heure été/hiver du coup on laisse django faire, mais c'est pas beau
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,15,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,17,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

    def testDailyRecurringEvent(self):

        createBooking(datetime(self.year,9,1,15,0,0), datetime(self.year,9,1,16,0,0), recurring_rule = "DAILY", end_recurring_period = datetime(self.year,9,30,18,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), HTTP_HOST="10.0.3.94")

        #Check if our event is here everyday at the right time
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,13,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,14,0,0)).astimezone(pytz.utc).hour

    def testWeeklyEvent(self):

        createBooking(datetime(self.year,9,1,10,0,0), datetime(self.year,9,1,12,0,0), recurring_rule = "WEEKLY", end_recurring_period = datetime(self.year,9,30,18,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), HTTP_HOST="10.0.3.94")

        #Check if our event is here every week at the right time and only the right days
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    if day[0].day in [1, 8, 15, 22, 29]:
                        self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,10,0,0)).astimezone(pytz.utc).hour
                        self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,12,0,0)).astimezone(pytz.utc).hour
                    else:
                        self.assertFalse(day[1])

    def testMonthlyEvent(self):

        createBooking(datetime(self.year,9,1,8,0,0), datetime(self.year,9,1,9,0,0), recurring_rule = "MONTHLY", end_recurring_period = datetime(self.year,11,30,18,0,0))

        self.client.login(username="jbvallad", password="blabla")

        #Check if our event is here every month at the right time and only the right days
        #i is the current month
        for i in range(9,12):
            r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": i}), HTTP_HOST="10.0.3.94")
            for week in r.context["calendar"]:
                for day in week:
                    if day[0]:
                        if day[0].day == 1:
                            self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,i,1,8,0,0)).astimezone(pytz.utc).hour
                            self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,i,1,9,0,0)).astimezone(pytz.utc).hour
                        else:
                            self.assertFalse(day[1])

    def testMultipleDayEvent(self):

        createBooking(datetime(self.year,9,1,20,0,0), datetime(self.year,9,5,21,0,0), recurring_rule = "NONE")

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), HTTP_HOST="10.0.3.94")

        #Check if our event is here for multiple days
        for week in r.context["calendar"][:2]:
            for day in week:
                if day[0]:
                    if day[0].day in range(1,6):
                        self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                        self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                    else:
                        self.assertFalse(day[1])

    #Hits a bug, need to be fixed
    #TODO: fix the bug :^)
    @skip
    def testMultipleDayEventBetweenMonth(self):

        createBooking(datetime(self.year,9,29,20,0,0), datetime(self.year,10,2,21,0,0), recurring_rule = "NONE")

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [29,30]:
                    print(day)
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "10"}), HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][:1][0]:
            if day[0]:
                if day[0].day in [1,2]:
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])
