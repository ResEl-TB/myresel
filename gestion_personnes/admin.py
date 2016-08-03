from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from gestion_personnes.models import LdapUser


class LdapUserAdmin(TranslationAdmin):
    list_display = (
        'hostname',
        'ip',
        'uid',
        'zone',
    )
    list_filter = ['zone']

admin.site.register(LdapUser, LdapUserAdmin)
