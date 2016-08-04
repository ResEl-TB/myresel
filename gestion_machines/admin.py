from django.contrib import admin

from gestion_machines.models import LdapDevice


@admin.register(LdapDevice)
class LdapDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'hostname',
        'ip',
        'owner',
        'zones',
    )
    list_filter = ['zones']

