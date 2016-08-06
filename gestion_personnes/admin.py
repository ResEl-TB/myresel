from django.contrib import admin

from gestion_personnes.models import LdapUser


@admin.register(LdapUser)
class LdapUserAdmin(admin.ModelAdmin):
    list_display = (
        'uid',
        'displayname',
        'promo',
        'mail',
        'batiment',
    )
    list_filter = ['promo', 'cotiz', 'batiment']

    search_fields = ['uid', 'mail',]
