import redis
import logging
from itertools import chain
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from myresel import settings
from gestion_personnes.models import LdapUser
from datetime import datetime, timedelta, date, time

logger = logging.getLogger("default")

class Command(BaseCommand):
    help = 'Create reminders emails for every members'

    def new_redis(self):
        self.r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
        )


    def is_email_in_redis(self, user, day):
        redis_key = "%s_%s_%s" % (
            settings.REMINDER_REDIS_PREFIX,
            user.uid,
            day.isoformat()[:-9])
        email_sent = self.r.get(redis_key)
        return email_sent

    def put_email_in_redis(self, user, day):
        redis_key = "%s_%s_%s" % (
            settings.REMINDER_REDIS_PREFIX,
            user.uid,
            day.isoformat()[:-9])
        email_sent = self.r.set(redis_key, 'email_sent')


    def get_user_day(self, day):
        one_day = timedelta(days=1)
        targeted_users = LdapUser.filter(
                end_cotiz__ge=day.strftime('%Y%m%d%H%M%SZ'),
                end_cotiz__lt=(day+one_day).strftime('%Y%m%d%H%M%SZ'))
        return targeted_users

    def new_reminder_email(self, user, day, expired=False):
        if not expired:
            days = user.end_cotiz - day
            content = render_to_string(
                    "tresorerie/mails/reminder.txt",
                    {'user': user, 'day': day,
                        'days': days, 'reminders': settings.REMINDERS_DAYS})
            subject = "[ResEl] Vos frais d'accès expirent dans %s jours" % days
        else:
            content = render_to_string(
                    "tresorerie/mails/expired.txt",
                    {'user': user, 'day': day})
            subject = "[ResEl] Vos frais d'accès ont expirés"

        email = EmailMessage(
            subject=subject,
            body=content,
            from_email=settings.TREASURER_EMAIL,
            to=[user.mail],
            reply_to=[settings.SUPPORT_EMAIL],
        )

        return {
            'user': user,
            'day': day,
            'content': email
        }


    def emails_gen(self, day, expired):
        targeted_users = self.get_user_day(day)
        for user in targeted_users:
            yield self.new_reminder_email(user, day, expired=expired)

    def send_emails(self, emails, dry=False):
        for email in emails:
            if self.is_email_in_redis(email['user'], email['day']):
                logger.warning("Today email already sent for user %s on day %s",
                    email['user'].uid,
                    email['day'].isoformat(),
                    extra={
                        'uid': email['user'].uid,
                        'address': email['user'].mail,
                        'day': email['day'].isoformat(),
                        'message_code': 'REMINDER_ALREADY_SENT',
                        })
                continue
            try:
                if not dry:
                    email['content'].send()
                    self.put_email_in_redis(email['user'], email['day'])
                else:
                    print(email['content'].body)
                logger.info("Reminder email sent to %s", email['user'].uid,
                        extra={
                            'uid': email['user'].uid,
                            'address': email['user'].mail,
                            'day': email['day'].isoformat(),
                            'message_code': 'REMINDER_SENT',
                            }
                        )
            except Exception as e:
                logger.error("Error while sending reminder to %s: %s",
                        email['user'].uid,
                        e,
                        extra={
                            'uid': email['user'].uid,
                            'address': email['user'].mail,
                            'day': email['day'].isoformat(),
                            'error': e,
                            'message_code': 'REMINDER_SENT',
                            }
                        )

    def handle(self, *args, **options):
        if not settings.REMINDERS_ACTIVATED:
            logger.warning("Reminders disabled in settings")
            print("Reminders disabled in settings")
            return
        self.new_redis()

        today = datetime.combine(date.today(), time())
        reminder_days = [today - timedelta(days=delta)
                for delta in settings.REMINDERS_DAYS]

        emails = iter(())
        # Reminders emails
        for day in reminder_days:
            emails = chain(emails, self.emails_gen(day, expired=False))

        # Payment expired emails
        if settings.REMINDER_EXPIRATION_DAY:
            emails = chain(emails, self.emails_gen(today, expired=True))

        self.send_emails(emails, dry=settings.REMINDER_DRY)

