from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from gestion_machines.models import LdapDevice


class LdapDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'uid',
        'displayname',
        'promo',
        'state',
        'mail',
        'batiment',
    )
    list_filter = ['promo', 'cotiz', 'batiment']

admin.site.register(LdapDevice, LdapDeviceAdmin)
