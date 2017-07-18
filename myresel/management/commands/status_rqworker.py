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
        error_output = "MYRESEL CRITICAL:\n"

        for service in services:
            try:
                out = subprocess.check_output(["systemctl", "is-active", service]).decode()
            except FileNotFoundError as e:
                is_error = True
                error_output += "Cannot execute systemctl is-active %s\n" % service
            except subprocess.CalledProcessError as e:
                is_error = True
                error_output += "%s is %s\n" % (service, e.output.decode().strip())

            if not re.match(regex, out):
                is_error = True
                error_output += "%s is %s\n" % (service, out)

        if is_error:
            raise CommandError(error_output)
        else:
            self.stdout.write(self.style.SUCCESS('MYRESEL OK: All services running'))
