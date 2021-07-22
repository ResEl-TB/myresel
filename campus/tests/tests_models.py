from django.test import TestCase
from django.core import mail
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from datetime import timedelta
from unittest import skip
import pytz
from campus.models import RoomBooking, Room
from gestion_personnes.tests import create_full_user

class RoomBookingTestCase(TestCase):
    def setUp(self):
        user = create_full_user()

        # Creating room located in the Foyer
        room_f = Room()
        room_f.location = 'F'
        room_f.name = 'Salle TV'
        room_f.mailing_list = 'morgan@robin.wf'
        room_f.save()

        # Booking that room
        booking_f = RoomBooking()
        booking_f.name = 'Forma ResEl'
        booking_f.description = 'Configuration de switchs'
        booking_f.start_time = timezone.now()
        booking_f.end_time = booking_f.start_time + timedelta(hours=2)
        booking_f.user = user.uid
        booking_f.booking_type = 'training'
        booking_f.save()
        booking_f.room.add(room_f)

        # Creating room located in the school
        room_s = Room()
        room_s.location = 'S'
        room_s.name = 'Grand amphi'
        room_s.mailing_list = 'morgan@robin.wf'
        room_s.save()

        # Booking that room
        booking_s = RoomBooking()
        booking_s.name = 'StudentOrganisation ciné'
        booking_s.description = 'Visionnage de films X'
        booking_s.start_time = timezone.now()
        booking_s.end_time = booking_s.start_time + timedelta(hours=2)
        booking_s.user = user.uid
        booking_s.booking_type = 'party'
        booking_s.save()
        booking_s.room.add(room_s)

    @skip("Since django_rq is used, don't know how to test that ...")
    def test_notify_mailing_list(self):
        # Since this is a room in the Foyer, no mail should be sent
        booking_f = RoomBooking.objects.get(name='Forma ResEl')
        booking_f.notify_mailing_list()
        self.assertEqual(len(mail.outbox), 0)

        # Testing for a room located in the school - should send a mail
        booking_s = RoomBooking.objects.get(name='StudentOrganisation ciné')
        booking_s.notify_mailing_list()
        self.assertEqual(len(mail.outbox), 1)

class RoomTestCase(TestCase):
    def setUp(self):
        # Creating room located in the Foyer
        room_f = Room()
        room_f.location = 'F'
        room_f.name = 'Salle TV'
        room_f.mailing_list = 'morgan@robin.wf'
        room_f.save()

    def test_is_free(self):
        room = Room.objects.get(name='Salle TV')
        booking = RoomBooking()
        booking.name = 'Forma ResEl'
        booking.description = 'Config de switchs'
        booking.user = 'mrobin'
        booking.booking_type = 'training'
        booking.start_time = parse_datetime('2016-12-01T10:00:00Z')
        booking.end_time = parse_datetime('2016-12-01T11:00:00Z')
        booking.save()
        booking.room.add(room)

        # Room should be free
        self.assertTrue(
            room.is_free(
                parse_datetime('2016-12-01T09:00:00Z'),
                parse_datetime('2016-12-01T09:30:00Z')
            )
        )

        # Room should be occupied
        self.assertFalse(
            room.is_free(
                parse_datetime('2016-12-01T09:15:00Z'),
                parse_datetime('2016-12-01T10:30:00Z')
            )
        )

        # Room should be occupied
        self.assertFalse(
            room.is_free(
                parse_datetime('2016-12-01T10:15:00Z'),
                parse_datetime('2016-12-01T10:30:00Z')
            )
        )

    def test_multiple_days_event_is_free(self):
        room = Room.objects.get(name='Salle TV')
        booking = RoomBooking()
        booking.name = 'Art Live'
        booking.description = 'Config de switchs'
        booking.user = 'jhomassel'
        booking.booking_type = 'training'
        booking.start_time = parse_datetime('2016-11-01T10:00:00Z')
        booking.end_time = parse_datetime('2016-11-03T11:00:00Z')
        booking.save()
        booking.room.add(room)

        # Room should be free
        self.assertTrue(
            room.is_free(
                parse_datetime('2016-11-03T12:00:00Z'),
                parse_datetime('2016-11-03T13:00:00Z')
            )
        )

        # Room should be occupied
        self.assertFalse(
            room.is_free(
                parse_datetime('2016-11-02T09:15:00Z'),
                parse_datetime('2016-11-02T10:30:00Z')
            )
        )
