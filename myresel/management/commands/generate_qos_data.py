import itertools
import random

import time
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from gestion_personnes.models import LdapUser


class Command(BaseCommand):
    pass
