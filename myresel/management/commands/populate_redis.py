from django.core.management.base import BaseCommand, CommandError
from myresel import settings
import redis

class Command(BaseCommand):
    help = 'Generate data for the redis server'

    def handle(self, *args, **options):
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
            )
            for net in settings.DEBUG_SETTINGS['networks']:
                r.set('mac__%s' % settings.DEBUG_SETTINGS['networks'][net]['client_fake_ip'],  settings.DEBUG_SETTINGS['mac'])
        except redis.exceptions.ConnectionError as e:
            raise CommandError('REDIS ERROR : %s' % e)
