import redis
from unittest import skipUnless
from io import StringIO
from datetime import datetime, timedelta, date, time
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.conf import settings

from gestion_personnes.tests import create_full_user, try_delete_user
from myresel.management.commands import fees_reminder

class FeesReminderTest(TestCase):
    def _create_date_user(self, fees_expire_in):
         user = create_full_user(
                 uid="remuser%i" % fees_expire_in,
                 email="fdsfdsf%i@telecom-bretagne.eu" % fees_expire_in)
         user.end_cotiz = self.now + timedelta(days=fees_expire_in)
         try_delete_user(user.uid)
         user.save()
         return user

    def clean_redis(self):
       r = redis.Redis(
           host=settings.REDIS_HOST,
           port=settings.REDIS_PORT,
           password=settings.REDIS_PASSWORD,
       )
       for k in r.keys("%s*" % settings.REMINDER_REDIS_PREFIX):
           r.delete(k)


    def setUp(self):
        self.margin = 5
        REMINDERS_DAYS = settings.REMINDERS_DAYS
        self.now = datetime.now()
        self.today =  datetime.combine(date.today(), time())

        self.reminded_users = [self._create_date_user(d) for d in REMINDERS_DAYS]
        self.not_reminded_users = [
            self._create_date_user(max(REMINDERS_DAYS) + 5),
            self._create_date_user(min(REMINDERS_DAYS) - 5),
        ]
        self.not_reminded_users += [
                self._create_date_user(d)
                for d in range(min(REMINDERS_DAYS), max(REMINDERS_DAYS))
                    if d not in REMINDERS_DAYS
        ]

        self.clean_redis()


    def test_get_user_day(self):
        c = fees_reminder.Command()
        for i, d in enumerate(settings.REMINDERS_DAYS):
            day = self.today + timedelta(days=d)
            targeted_users = c.get_user_day(day)
            uids = [u.uid for u in targeted_users]
            self.assertIn(self.reminded_users[i].uid, uids)
            for u in self.not_reminded_users:
                self.assertNotIn(u.uid, uids)


    @skipUnless(not settings.REMINDER_DRY and settings.REMINDERS_ACTIVATED,
            "Test needs the reminder be activated")
    def test_command_default(self):
        # out = StringIO()
        # call_command('fees_reminder', stdout=out)
        fees_reminder.Command().handle()
        dests = [t for e in mail.outbox for t in e.to]
        for u in self.reminded_users:
                self.assertIn(u.mail, dests)
        for u in self.not_reminded_users:
                self.assertNotIn(u.mail, dests)
