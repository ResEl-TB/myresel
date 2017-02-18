import itertools
import random

import time
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from devices.models import PeopleHistory, PeopleData
from gestion_personnes.models import LdapUser


class Command(BaseCommand):
    help = 'Generate dummy data for qos module'

    NBR_POINTS = 100000
    TIME = 60 * 60 * 24 * 7

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='*', type=str)

    def create_data(self, user):
        for nbr in range(self.NBR_POINTS):
            for way_t, flow_t in itertools.product(PeopleHistory.WAY_CHOICES, PeopleHistory.FLOW_CHOICES):
                hist = PeopleHistory()
                data = PeopleData()

                hist.site = "Brest"
                hist.timestamp = int(time.time()) - random.randint(0, self.TIME)
                hist.cn = user.pk
                hist.uid = user.uid
                hist.way = way_t[0]
                hist.flow = flow_t[0]
                hist.group = 0
                hist.amount = 1000000 + random.randint(-100000, 100000)
                hist.amount_ponderated = hist.amount
                hist.duration = 1
                try:
                    hist.save(force_insert=True)
                except IntegrityError:
                    pass

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