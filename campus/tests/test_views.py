# -*- coding: utf-8 -*-
from unittest import skip

from datetime import date, datetime
import pytz
from django.utils import timezone

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from gestion_personnes.models import LdapUser, LdapGroup
from gestion_personnes.tests import create_full_user, try_delete_user

from campus.models.clubs_models import StudentOrganisation, Association, ListeCampagne
from campus.models.rooms_models import Room, RoomBooking
from campus.forms import ClubManagementForm, ClubEditionForm, RoomBookingForm, AddRoomForm


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
        user.inscr_date = datetime.now().astimezone()
        user.save()

        self.client.login(username="lcarr", password="blah")

    def test_load_create_simple_email(self):
        r = self.client.get(reverse("campus:mails:send"),
                            ZONE="Brest-any", HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)

    @skip("View not ready, crsf error")  # TODO: don't forget to reactivate the test
    def test_create_simple_email(self):
        r = self.client.get(reverse("campus:mails:send"),
                        ZONE="Brest-any", HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "campus/mails/send_mail.html")

        r = self.client.post(
            reverse("campus:mails:send"),
            ZONE="Brest-any", HTTP_HOST="10.0.3.94", follow=True,
            data={
                "sender": "loic.carr@resel.fr",
                "subject": "fuu",
                "content": "Wheyudsf  dsqj dsq LOREM IPSUM",
            })

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertEqual(2, len(mail.outbox))

#######################################
########### Club management ###########
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

class ClubHomeTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        populate_orgas()

    def testLoadWithoutUser(self):
        r = self.client.get(reverse("campus:clubs:list"),
                                   ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "campus/clubs/list.html")

    def testLoadWithUser(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:list"),
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)

class DetailTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        populate_orgas()

    def testLoadWithoutUser(self):
        r = self.client.get(reverse("campus:clubs:club_detail", kwargs={"pk":"tenniscn"}),
                                   ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "campus/clubs/detail.html")

    def testLoadWithUser(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:club_detail", kwargs={"pk":"tenniscn"}),
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94")
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
            ZONE="Brest-any", HTTP_HOST="10.0.3.94",
            follow = True
        )

    def testSimpleLoad(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:clubs:my-clubs"), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertTemplateUsed(r, "campus/clubs/list.html")

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
        form.data["name"] = "Club Tennis"
        self.assertTrue(form.is_valid())
        form.edit_club(form.data["cn"])
        club = StudentOrganisation.get(cn=form.data["cn"])
        self.assertTrue(club.name == "Club Tennis")

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
        r = self.client.post(reverse("campus:clubs:add-person", kwargs={'pk':self.cn}),
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).members)

    def testAddSomeone(self):
        r = self.client.post(reverse("campus:clubs:add-person", kwargs={'pk':self.cn}),
                                    data={"id_user":"bvallad"},
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).members)

class RemovePersonTestCase(TestCase):

    def setUp(self):
        populate_orgas()
        self.cn = "tenniscn"
        club=StudentOrganisation.get(cn=self.cn)

        try_delete_user("jbvallad")
        try_delete_user("bvallad")
        try_delete_user("vallad")

        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        LdapGroup.get(pk='campusmodo').add_member(user.pk)
        club.members.append(user.pk)

        user = create_full_user(uid="bvallad", pwd="blabla")
        user.save()
        club.members.append(user.pk)

        user = create_full_user(uid="vallad", pwd="blabla")
        user.save()
        club.members.append(user.pk)

        club.save()

        self.client.login(username="vallad", password="blabla")

    def testRemoveSelf(self):
        # We just make sure that there is something to remove
        self.assertTrue(LdapUser.get(uid="vallad").pk in StudentOrganisation.get(cn=self.cn).members)
        r=self.client.post(reverse("campus:clubs:remove-person", kwargs={"pk":self.cn}),
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94", HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(LdapUser.get(uid="vallad").pk in StudentOrganisation.get(cn=self.cn).members)
        self.assertEqual(1, len(mail.outbox))

    def testRemoveSomeone(self):
        self.client.login(username="jbvallad", password="blabla")
        self.assertTrue(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).members)
        r=self.client.post(reverse("campus:clubs:remove-person", kwargs={"pk":self.cn}),
                                    data={"id_user":"bvallad"}, ZONE="Brest-any", HTTP_HOST="10.0.3.94",
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).members)
        self.assertEqual(1, len(mail.outbox))

class AddPrezTestCase(TestCase):

    def setUp(self):
        populate_orgas()
        self.cn = "tenniscn"
        club = StudentOrganisation.get(cn=self.cn)

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
        self.assertFalse(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).prezs)

        r = self.client.post(reverse("campus:clubs:add-prez", kwargs={'pk': self.cn}),
                                    data={"id_user": "bvallad"},
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94",
                                    follow=True,
                                    HTTP_REFERER=reverse('campus:clubs:list'))

        self.assertEquals(200, r.status_code)
        self.assertTrue(LdapUser.get(uid="bvallad").pk in StudentOrganisation.get(cn=self.cn).prezs)

    def testAddPrezBeingPrez(self):
        self.client.login(username="vallad", password="blabla")
        self.assertFalse(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).prezs)
        r = self.client.post(reverse("campus:clubs:add-prez", kwargs={'pk': self.cn}),
                                    data={"id_user": "jbvallad"},
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94",
                                    follow=True,
                                    HTTP_REFERER=reverse('campus:clubs:list'))

        self.assertEquals(200, r.status_code)
        self.assertTrue(LdapUser.get(uid="jbvallad").pk in StudentOrganisation.get(cn=self.cn).prezs)

    def testAddPrezBeingNobody(self):
        self.client.login(username="allad", password="blabla")
        self.assertFalse(LdapUser.get(uid="allad").pk in StudentOrganisation.get(cn=self.cn).prezs)
        r = self.client.post(reverse("campus:clubs:add-prez", kwargs={'pk': self.cn}),
                                    data={"id_user": "allad"},
                                    ZONE="Brest-any", HTTP_HOST="10.0.3.94",
                                    follow=True,
                                    HTTP_REFERER=reverse('campus:clubs:list'))

        self.assertEquals(200, r.status_code)
        self.assertFalse(LdapUser.get(uid="allad").pk in StudentOrganisation.get(cn=self.cn).prezs)

class DeleteClubTestCase(TestCase):

    def setUp(self):
        populate_orgas()

        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        LdapGroup.get(pk='campusmodo').add_member(user.pk)

    def testDeleteClubBeingModo(self):
        self.client.login(username="jbvallad", password="blabla")
        self.assertTrue(StudentOrganisation.filter(cn="tenniscn"))
        r = self.client.post(
            reverse("campus:clubs:delete",
                    kwargs={'pk':'tenniscn'}),
                    ZONE="Brest-any", HTTP_HOST="10.0.3.94",
                    follow=True
            )

        self.assertEquals(200, r.status_code)
        self.assertFalse(StudentOrganisation.filter(cn="tenniscn"))

################################
########### Calendar ###########
################################

def createRoom(clubs=[], private=False):

    room = Room(
        location="F",
        name="Salle piano",
        mailing_list = "piano@resel.fr",
        private = private,
        clubs = clubs,
    )
    room.save()
    return(room)

# pylint: disable=no-member
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

    room = createRoom()

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

def createBookingForm(rooms=[1], name="Booking", description="Automaticaly Generated", start_time=None, end_time=None, booking_type="club", recurring_rule="NONE", end_recurring_period="", displayable=True):

    year = date.today().year+1

    if start_time == None:
        start_time = "%s-12-10 01:00:00"% year
    if end_time == None:
        end_time = "%s-12-10 23:00:00"% year

    form = RoomBookingForm(data={
        'room': rooms,
        'name': name,
        'description': description,
        'start_time': start_time,
        'end_time': end_time,
        'booking_type': booking_type,
        'recurring_rule': recurring_rule,
        'end_recurring_period': end_recurring_period,
        'displayable': displayable,
    })
    return(form)

def createRoomForm(location="F", name="Generated", mailing_list="", private=False, clubs=""):

    form = AddRoomForm(data={
        'location': location,
        'name': name,
        'mailing_list': mailing_list,
        'private': private,
        'clubs': clubs,
    })

    return(form)

class CalendarTestCase(TestCase):
    """
    This test covers many booking cases
    Many month, days etc are hardcoded, but unless earth get invaded or this kind of shit,
    we're pretty safe and can assume that the gregorian calendar and its standards are not
    going to change anytime soon. These hardcoded things are number of days in a specific month and
    similar things
    """

    #we setUp a var with next year because our booking isn't valid if
    #it's prior to the current date.
    year = date.today().year+1

    def setUp(self):

        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()

    def testSimpleEvent(self):

        createBooking(datetime(self.year,9,1,18,0,0), datetime(self.year,9,1,19,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")

        #Check if our event is at the right time and only at the right day
        for day in r.context["calendar"][0]:
            if day[0]:
                if day[0].day == 1:
                    self.assertTrue(day[1])
                    #J'ai trouvé mieux pour convertir une heure en utc, car python ne gère pas heure été/hiver
                    #ne gère pas heure été/hiver du coup on laisse django faire, mais c'est pas beau
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,15,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,17,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

    def testDailyRecurringEvent(self):

        createBooking(datetime(self.year,9,1,15,0,0), datetime(self.year,9,1,16,0,0), recurring_rule = "DAILY", end_recurring_period = datetime(self.year,9,30,18,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")

        #Check if our event is here everyday at the right time
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,13,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,14,0,0)).astimezone(pytz.utc).hour

    def testWeeklyEvent(self):

        createBooking(datetime(self.year,9,1,10,0,0), datetime(self.year,9,1,12,0,0), recurring_rule = "WEEKLY", end_recurring_period = datetime(self.year,9,30,18,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")

        #Check if our event is here every week at the right time and only the right days
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    if day[0].day in [1, 8, 15, 22, 29]:
                        self.assertTrue(day[1])
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
            r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": i}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
            for week in r.context["calendar"]:
                for day in week:
                    if day[0]:
                        if day[0].day == 1:
                            self.assertTrue(day[1])
                            self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,i,1,8,0,0)).astimezone(pytz.utc).hour
                            self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,i,1,9,0,0)).astimezone(pytz.utc).hour
                        else:
                            self.assertFalse(day[1])

    def testDailyRecurringEventBetweenMonth(self):

        #daily, weekly, monthly, they work the same way so we only test for daily,
        #adjust if necessary
        createBooking(datetime(self.year,9,29,8,0,0), datetime(self.year,9,29,9,0,0), recurring_rule = "DAILY", end_recurring_period = datetime(self.year,10,2,18,0,0))

        self.client.login(username="jbvallad", password="blabla")

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": 9}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [29,30]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,8,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,9,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": 10}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [1,2]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,8,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,9,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

    def testDailyRecurringEventBetweenYear(self):

        createBooking(datetime(self.year,12,29,8,0,0), datetime(self.year,12,29,9,0,0), recurring_rule = "DAILY", end_recurring_period = datetime(self.year+1,1,2,18,0,0))

        self.client.login(username="jbvallad", password="blabla")

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": 12}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [29,30,31]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,8,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,9,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year+1, "month": 1}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [1,2]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,8,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,9,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

    def testMultipleDayEvent(self):

        createBooking(datetime(self.year,9,1,20,0,0), datetime(self.year,9,5,21,0,0), recurring_rule = "NONE")

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")

        #Check if our event is here for multiple days
        for week in r.context["calendar"][:2]:
            for day in week:
                if day[0]:
                    if day[0].day in range(1,6):
                        self.assertTrue(day[1])
                        self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                        self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                    else:
                        self.assertFalse(day[1])

    def testMultipleDayEventBetweenMonth(self):

        createBooking(datetime(self.year,9,29,20,0,0), datetime(self.year,10,2,21,0,0), recurring_rule = "NONE")

        self.client.login(username="jbvallad", password="blabla")

        #Checks if our event is here on both month
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [29,30]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "10"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][:1][0]:
            if day[0]:
                if day[0].day in [1,2]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

    def testMultipleMonthEvent(self):

        createBooking(datetime(self.year,9,10,20,0,0), datetime(self.year,11,15,21,0,0), recurring_rule = "NONE")

        self.client.login(username="jbvallad", password="blabla")

        #Checks if our event is present for the right days, especialy
        #for the month between the two others
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "9"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    if day[0].day in range(10,31):
                        self.assertTrue(day[1])
                        self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                        self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                    else:
                        self.assertFalse(day[1])

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "10"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "11"}), ZONE="Brest-any", HTTP_HOST="11.0.3.94")
        for week in r.context["calendar"]:
            for day in week:
                if day[0]:
                    if day[0].day in range(1,16):
                        self.assertTrue(day[1])
                        self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                        self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                    else:
                        self.assertFalse(day[1])

    def testMultipleDayEventBetweenYear(self):

        createBooking(datetime(self.year,12,29,20,0,0), datetime(self.year+1,1,2,21,0,0), recurring_rule = "NONE")

        self.client.login(username="jbvallad", password="blabla")

        #Checks if our event is here on both month from both years
        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year, "month": "12"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][-1:][0]:
            if day[0]:
                if day[0].day in [29,30,31]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

        r = self.client.get(reverse("campus:rooms:calendar-month", kwargs={"year": self.year+1, "month": "1"}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        for day in r.context["calendar"][:1][0]:
            if day[0]:
                if day[0].day in [1,2]:
                    self.assertTrue(day[1])
                    self.assertTrue(day[1][0].start_time.hour) == timezone.make_aware(datetime(self.year,9,1,20,0,0)).astimezone(pytz.utc).hour
                    self.assertTrue(day[1][0].end_time.hour) == timezone.make_aware(datetime(self.year,9,1,21,0,0)).astimezone(pytz.utc).hour
                else:
                    self.assertFalse(day[1])

class BookingFormTestCase(TestCase):
    """
    Tests if the booking form only saves correct info
    """

    year = date.today().year+1

    def setUp(self):

        populate_orgas(club_cn="club-test")

        try_delete_user("jbvallad")
        try_delete_user("bvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        user = create_full_user(uid="bvallad", pwd="blabla")
        user.save()

    def testValidForm(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom()
        form = createBookingForm(rooms=[room.id])

        self.assertTrue(form.is_valid())

    @skip("View not working anymore") #TODO: fix it
    def testCreatorCanManage(self):
        booking = createBooking(datetime(self.year,9,1,18,0,0), datetime(self.year,9,1,19,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:mod-booking", kwargs={'booking': booking.id}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")

        self.assertTemplateUsed(r, 'campus/rooms/booking.html')

    def testPlebsCantManage(self):
        self.client.login(username="jbvallad", password="blabla")
        booking = createBooking(datetime(self.year,1,1,18,0,0), datetime(self.year,1,1,19,0,0))

        self.client.login(username="bvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:mod-booking", kwargs={'booking': booking.id}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertEqual(r.status_code, 302)
        self.assertTemplateNotUsed(r, 'calendar.html')

    def testValidRecurrentForm(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom()

        form = createBookingForm(rooms=[room.id], recurring_rule="DAILY", end_recurring_period="%s-12-25 12:00:00"%self.year)
        self.assertTrue(form.is_valid())

        form = createBookingForm(rooms=[room.id], recurring_rule="WEEKLY", end_recurring_period="%s-12-25 12:00:00"%self.year)
        self.assertTrue(form.is_valid())

        form = createBookingForm(rooms=[room.id], recurring_rule="MONTHLY", end_recurring_period="%s-12-25 12:00:00"%self.year)
        self.assertTrue(form.is_valid())

    def testEndTimePriorToStartTime(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom()
        start_time = "%s-12-10 12:00:00"% self.year
        end_time = "%s-12-10 01:00:00"% self.year
        form = createBookingForm(rooms=[room.id], start_time=start_time, end_time=end_time)

        self.assertFalse(form.is_valid())

    def testInvalidStartTime(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom()
        start_time = "%s-16-10 12:00:00"% self.year
        form = createBookingForm(rooms=[room.id], start_time=start_time)

        self.assertFalse(form.is_valid())

    def testInvalidEndTime(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom()
        end_time = "%s-16-10 12:00:00"% self.year
        form = createBookingForm(rooms=[room.id], start_time=end_time)

        self.assertFalse(form.is_valid())

    def testAllowedRoom(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom(clubs="club-test", private=True)

        form = createBookingForm(rooms=[room.id])
        self.assertFalse(form.is_valid())


    def testForbidenRoom(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom(clubs="club-test", private=True)

        form = createBookingForm(rooms=[room.id])
        self.assertFalse(form.is_valid())

    def testEmptyFields(self):
        self.client.login(username="jbvallad", password="blabla")
        room = createRoom()

        form = createBookingForm(rooms=[])
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], name="")
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], description="")
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], start_time="")
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], end_time="")
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], booking_type="")
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], recurring_rule="")
        self.assertFalse(form.is_valid())

        form = createBookingForm(rooms=[room.id], recurring_rule="DAILY", end_recurring_period="")
        self.assertFalse(form.is_valid())


class RoomFormTestCase(TestCase):

    def setUp(self):
        populate_orgas(club_cn="club-test")

        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()

    def testValidForm(self):
        self.client.login(username="jbvallad", password="blabla")
        form = createRoomForm()
        self.assertTrue(form.is_valid())

    def testBadMail(self):
        self.client.login(username="jbvallad", password="blabla")
        form = createRoomForm(mailing_list="testresel.fr")
        self.assertFalse(form.is_valid())

    def testKnownClub(self):
        self.client.login(username="jbvallad", password="blabla")
        form = createRoomForm(clubs="club-test")
        self.assertTrue(form.is_valid())

    def testUnknownClub(self):
        self.client.login(username="jbvallad", password="blabla")
        form = createRoomForm(clubs="udhezohiez")
        self.assertFalse(form.is_valid())

    def testWrongLocation(self):
        self.client.login(username="jbvallad", password="blabla")
        form = createRoomForm(location="42")
        self.assertFalse(form.is_valid())

    def testEmptyField(self):
        self.client.login(username="jbvallad", password="blabla")

        form = createRoomForm(name="")
        self.assertFalse(form.is_valid())

        form = createRoomForm(location="")
        self.assertFalse(form.is_valid())

class EventDetailTestCase(TestCase):

    year = date.today().year+1

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()

    def testSimpleLoad(self):

        booking = createBooking(datetime(self.year,9,1,18,0,0), datetime(self.year,9,1,19,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:rooms:booking-detail", kwargs={'slug': booking.id}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertEqual(r.status_code, 200)

class DeleteEventTestCase(TestCase):

    year = date.today().year+1

    def setUp(self):
        try_delete_user("jbvallad")
        try_delete_user("vallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()
        LdapGroup.get(pk='campusmodo').add_member(user.pk)
        user = create_full_user(uid="vallad", pwd="blabla")
        user.save()

    def testSimpleDeletion(self):
        booking = createBooking(datetime(self.year,9,1,18,0,0), datetime(self.year,9,1,19,0,0))

        self.client.login(username="jbvallad", password="blabla")
        r = self.client.post(reverse("campus:rooms:delete-booking", kwargs={'pk': booking.id}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertFalse(RoomBooking.objects.all().filter(id=booking.id))

    def testForbidenDeletion(self):
        booking = createBooking(datetime(self.year,9,1,18,0,0), datetime(self.year,9,1,19,0,0))

        self.client.login(username="vallad", password="blabla")
        r = self.client.post(reverse("campus:rooms:delete-booking", kwargs={'pk': booking.id}), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertTrue(RoomBooking.objects.all().filter(id=booking.id))

class CampusHomeTestCase(TestCase):

    def setUp(self):
        try_delete_user("jbvallad")
        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.save()

    def testSimpleLoad(self):
        self.client.login(username="jbvallad", password="blabla")
        r = self.client.get(reverse("campus:home"), ZONE="Brest-any", HTTP_HOST="10.0.3.94")
        self.assertEqual(r.status_code, 200)

# AE Admin ajax tests

class AEAjaxTestCase(TestCase):
    def setUp(self):
        try_delete_user("jdoe")
        try_delete_user("jbvallad")

        user = LdapUser()
        user.uid = 'jdoe'
        user.first_name = "John"
        user.last_name = "Doe"
        user.user_password = "blah"
        user.mail = "jogn.doe@resel.fr"
        user.promo = 2016
        user.n_adherent = "16156"
        user.dates_membre = ["20160901-20170831"]
        user.nt_password = user.user_password
        user.inscr_date = datetime.now().astimezone()
        user.save()

        user = create_full_user(uid="jbvallad", pwd="blabla")
        user.ae_admin = True
        user.save()
        self.client.login(username="jbvallad", password="blabla")

    def testSimpleLoadAEAdmin(self):
        r = self.client.get(
            reverse("campus:ae-admin:home"),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue(r.status_code == 200)

    def testPlebsCannotAccess(self):
        user = LdapUser.get(pk="jdoe")
        user.ae_admin = False
        user.save()
        self.client.login(username="jdoe", password="blah")
        r = self.client.get(
            reverse("campus:ae-admin:home"),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue(r.status_code == 302)

    def testSimpleAEMemberSearch(self):
        r = self.client.get(
            reverse("campus:ae-admin:search-members"),
            {'filter': 'john'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue(r.status_code == 200)
        self.assertFalse(r.json().get('error', False))
        self.assertTrue(len(r.json()['results']) >= 1)


    def testSimpleAEMemberEmptySearch(self):
        r = self.client.get(
            reverse("campus:ae-admin:search-members"),
            {'filter': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('results', False))

    def testAEMemberSpecialSearchFormer(self):
        user = LdapUser.get(pk='jdoe')
        user.dates_membre = ["20160901-20160831"]
        user.save()
        r = self.client.get(
            reverse("campus:ae-admin:search-members"),
            {'filter': 'john', 'special': 'true', 'search_type': 'former'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue('jdoe' in (el['uid'] for el in r.json().get('results', [])))

    def testAEMemberSpecialSearchCurrent(self):
        user = LdapUser.get(pk='jdoe')
        user.dates_membre = ["20160901-20160831"]
        user.save()
        r = self.client.get(
            reverse("campus:ae-admin:search-members"),
            {'filter': 'john', 'special': 'true', 'search_type': 'current'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse('jdoe' in (el['uid'] for el in r.json().get('results', [])))

    def testSimpleCSVImport(self):
        user = LdapUser.get(pk='jdoe')
        r = self.client.post(
            reverse("campus:ae-admin:edit-user"),
            {
                'uid': 'jdoe',
                'start': '20160901',
                'end': '20170820',
                'first_name': "John",
                'last_name': "Doe",
                'n_adherent': "16156",
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        user_updated = LdapUser.get(pk='jdoe')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json().get('error', False))
        self.assertNotEqual(user_updated.dates_membre[-1], user.dates_membre[-1])

    def testInvalidDatesCSVImport(self):
        user = LdapUser.get(pk='jdoe')
        # Some invalid dates that the system is supposed to catch
        invalid_start_dates = [
            '201609011', #Too long
            '2016090',   #Too short
            '00000901',  #Invalid year
            '20161301',  #Invalid month
            '20160932',  #Invalid day
            '20160a011'  #Invalid caracter
        ]
        for start in invalid_start_dates:
            r = self.client.post(
                reverse("campus:ae-admin:edit-user"),
                {
                    'uid': 'jdoe',
                    'start': start,
                    'end': '20170810',
                    'first_name': "John",
                    'last_name': "Doe",
                    'n_adherent': "16156",
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                ZONE="Brest-any", HTTP_HOST="10.0.3.94"
            )
            user_updated = LdapUser.get(pk='jdoe')
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json().get('error', False))
            self.assertEqual(user_updated.dates_membre[-1], user.dates_membre[-1])

    def testInvalidUserCSVImport(self):
        r = self.client.post(
            reverse("campus:ae-admin:edit-user"),
            {
                'uid': 'jdoeeeeeee',
                'start': '20160901',
                'end': '20170820',
                'first_name': "John",
                'last_name': "Doe",
                'n_adherent': "16156",
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get('error', False))

    def testSimpleAEAdminAddition(self):
        user = LdapUser.get(pk='jdoe')
        user.ae_admin = False
        user.save()
        r = self.client.post(
            reverse("campus:ae-admin:add-admin"),
            {'uid': 'jdoe'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        user_updated = LdapUser.get(pk='jdoe')
        self.assertTrue(r.status_code == 200)
        self.assertFalse(r.json().get('error', False))
        self.assertTrue(user_updated.ae_admin)

    def testInvalidAEAdminAddition(self):
        r = self.client.post(
            reverse("campus:ae-admin:add-admin"),
            {'uid': 'jdoooooooooe'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue(r.status_code == 200)
        self.assertTrue(r.json().get('error', False))

    def testAlreadyAEAdminAddition(self):
        user = LdapUser.get(pk='jdoe')
        user.ae_admin = True
        user.save()
        r = self.client.post(
            reverse("campus:ae-admin:add-admin"),
            {'uid': 'jdoe'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        user_updated = LdapUser.get(pk='jdoe')
        self.assertTrue(r.status_code == 200)
        self.assertTrue(r.json().get('error', False))

    def testSimpleAdminRemoval(self):
        user = LdapUser.get(pk='jdoe')
        user.ae_admin = True
        user.save()
        r = self.client.post(
            reverse("campus:ae-admin:delete-admin"),
            {'uid': 'jdoe'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        user_updated = LdapUser.get(pk='jdoe')
        self.assertTrue(r.status_code == 200)
        self.assertFalse(r.json().get('error', False))
        self.assertFalse(user_updated.ae_admin)

    def testInvalidAdminRemoval(self):
        user = LdapUser.get(pk='jdoe')
        user.ae_admin = False
        user.save()
        r = self.client.post(
            reverse("campus:ae-admin:delete-admin"),
            {'uid': 'jdoe'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue(r.status_code == 200)
        self.assertTrue(r.json().get('error', False))

    def testInvalidAdminRemovalSelf(self):
        r = self.client.post(
            reverse("campus:ae-admin:delete-admin"),
            {'uid': 'jbvallad'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue(r.status_code == 200)
        self.assertTrue(r.json().get('error', False))

    def testGetAdmins(self):
        user = LdapUser.get(pk='jdoe')
        user.ae_admin = True
        user.save()
        r = self.client.get(
            reverse("campus:ae-admin:get-admins"),
            {'uid': 'jdoe'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertTrue('jdoe' in [u['uid'] for u in r.json().get('results', [])])

    def testSimpleUserAddition(self):
        try_delete_user("mx")
        r = self.client.post(
            reverse("campus:ae-admin:add-user"),
            {
                'first_name': "monsieur",
                'last_name': "x",
                'promo': "2019",
                'email': 'jdoe@imt-atlantique.fr',
                'training': 'FIG',
                'campus': 'Brest',
                'start': '20160901',
                'end': '20170820',
                'n_adherent': "16156",
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            ZONE="Brest-any", HTTP_HOST="10.0.3.94"
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json().get('error', False))
        try:
            LdapUser.get(pk="mx")
        except ObjectDoesNotExist:
            self.fail("User not created !")

    def testUserAdditionMissingAttributes(self):
        data = {
            'first_name': "monsieur",
            'last_name': "x",
            'promo': "2019",
            'email': 'jdoe@imt-atlantique.fr',
            'training': 'FIG',
            'campus': 'Brest',
            'start': '20160901',
            'end': '20170820',
            'n_adherent': "16156",
        }
        for i in range(len(data.keys())):
            data[list(data)[i]] = ""
            r = self.client.post(
                reverse("campus:ae-admin:add-user"),
                data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                ZONE="Brest-any", HTTP_HOST="10.0.3.94"
            )
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json().get('error', False))
