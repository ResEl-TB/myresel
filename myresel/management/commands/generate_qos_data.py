import itertools
import random

import time
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from gestion_machines.models import PeopleHistory, PeopleData
from gestion_personnes.models import LdapUser


class Command(BaseCommand):
    help = 'Generate dummy data for qos module'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='*', type=str)

    def create_data(self, user):
        for nbr in range(100):
            for way_t, flow_t in itertools.product(PeopleHistory.WAY_CHOICES, PeopleHistory.FLOW_CHOICES):
                hist = PeopleHistory()
                data = PeopleData()

                hist.site = "Brest"
                hist.timestamp = int(time.time()) - random.randint(0, 60 * 60 * 24)
                hist.cn = user.pk
                hist.uid = user.uid
                hist.way = way_t[0]
                hist.flow = flow_t[0]
                hist.group = 0
                hist.amount = 1000000
                hist.amount_ponderated = 1000000
                hist.duration = 1
                hist.save(force_insert=True)

    def handle(self, *args, **options):

        # Generate data for every body
        if len(options['username']) == 0:
            users = LdapUser.all()
            for user in users:
                self.create_data(user)
        else:
            for username in options['username']:
                try:
                    user = LdapUser.get(uid=username)
                    self.create_data(user)
                except ObjectDoesNotExist:
                    raise CommandError('User "%s" does not exist' % username)

        self.stdout.write(self.style.SUCCESS('Successfully created dummy data'))