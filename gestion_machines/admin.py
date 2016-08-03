from django.contrib import admin

from gestion_machines.models import LdapDevice


@admin.register(LdapDevice)
class LdapDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'hostname',
        'ip',
        'uid',
        'zone',
    )
    list_filter = ['zone']

