import redis
import ipaddress
import re
from django.core.management.base import BaseCommand, CommandError
from myresel import settings
from fonctions import ldap
from random import shuffle

class Command(BaseCommand):
    help = 'Generate the next free ips for the user network'

    def handle(self, *args, **options):
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
            )
            available_suffixes = set()
            ip_range = list(settings.NET_BREST_USERS.hosts())

            # La ligne qui suit est un putain hack de merde parce que le ResEl c'est de la merde
            # Apprennez à faire du réseau avant de faire des subnet.
            ip_range = [ip for ip in ip_range if re.match(r'^172\.22\.((2[01][0-9])|(22[0-3]))\.*', str(ip))]
            shuffle(ip_range)
            for ip in ip_range:
                ip_suffix = '.'.join(str(ip).split('.')[2:])
                if not ldap.search(settings.LDAP_DN_MACHINES, '(&(ipHostNumber=%s))' % ip_suffix):
                    available_suffixes.add(ip_suffix)
                if len(available_suffixes) >= settings.BUFFERED_AV_IPS:
                    break
            pipe = r.pipeline()
            pipe.delete(settings.REDIS_AV_IPS_KEY)
            for ip in available_suffixes:
                pipe.sadd(settings.REDIS_AV_IPS_KEY, ip)
            pipe.execute()

        except Exception as e:
            print(e)

