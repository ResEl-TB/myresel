# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError

import subprocess
import re

class Command(BaseCommand):
    help = 'Check rqworker status on production server using supervisord'

    def handle(self, *args, **options):
        try:
            out = subprocess.check_output(["supervisorctl", "status"]).decode()
        except FileNotFoundError as e:
            raise CommandError("RQWORKER CRITICAL: cannot execute supervisorctl")


        regex = re.compile(r"rqworker.*RUNNING")

        if re.match(regex, out):
            self.stdout.write(self.style.SUCCESS('RQWORKER OK: Worker running'))
        else:
            raise CommandError("RQWORKER CRITICAL: %s" % out)
