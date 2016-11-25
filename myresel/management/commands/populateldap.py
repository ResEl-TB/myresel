#!/usr/bin/env python3
# coding: utf-8

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Populate the ldap with initial data'

    def handle(self, *args, **options):
        import myresel.management.commands._populate_ldap
        self.stdout.write(self.style.SUCCESS('Successfully populated the database"'))
