# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError

import subprocess
import re

class Command(BaseCommand):
    help = 'Check website status on production server using systemd -- needs sudo privileges'

    def handle(self, *args, **options):
        services = [
            'rq-worker.service',
            'rq-scheduler.service',
            'nginx.service',
            'uwsgi.service',
            'cron.service',
        ]
        regex = re.compile(r"^active")
        is_error = False
        error_output = "MYRESEL CRITICAL: "

        for service in services:
            try:
                out = subprocess.check_output(["systemctl", "is-active", service]).decode()
                if not re.match(regex, out):
                    is_error = True
                    error_output += "%s is %s; " % (service, out)
            except FileNotFoundError as e:
                is_error = True
                error_output += "Can't execute 'systemctl is-active %s'; " % service
            except subprocess.CalledProcessError as e:
                is_error = True
                error_output += "%s is %s; " % (service, e.output.decode().strip())

        if is_error:
            raise CommandError(error_output)
        else:
            self.stdout.write(self.style.SUCCESS('MYRESEL OK: All services running'))

