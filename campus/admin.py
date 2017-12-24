# -*- coding: utf-8 -*-
"""
Django administration configuration for the campus module
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from campus.models import Room, RoomBooking, Mail
from campus.models import RoomAdmin as RoomAdministrator

class RoomBookingAdmin(admin.ModelAdmin):
    """
    Admin configuration for RoomBooking model
    """
    list_display = ('description', 'user', 'start_time', 'end_time', 'list_rooms')
    list_filter = ('room', 'start_time', 'end_time')
    search_fields = ('user',)

    # pylint: disable=no-self-use
    def list_rooms(self, booking):
        """
        List all the rooms of the given booking
        """
        html = '<p>'
        for room in booking.room.all():
            html += '%s<br>' % room.name
        html += '</p>'
        return format_html(mark_safe(html))
    list_rooms.short_description = 'salles'

class RoomAdmin(admin.ModelAdmin):
    """
    Admin configuration for Room model
    """
    list_display = ('name', 'location', 'private', 'list_clubs')
    list_filter = ('location', 'private')
    search_fields = ('name',)

    # pylint: disable=no-self-use
    def list_clubs(self, room):
        """
        List all the clubs allowed to access the Room
        """
        
        html = '<p>'
        for club in room.get_clubs():
            html += '%s<br>' % club
        html += '</p>'
        return format_html(mark_safe(html))
    list_clubs.short_description = 'clubs autorisés'

class RoomAdministratorAdmin(admin.ModelAdmin):
    """
    Admin configuration for RoomAdmin model 
    """
    list_display = ('user', 'list_rooms')

    # pylint: disable=no-self-use
    def list_rooms(self, administrator):
        """
        List all the rooms of the given booking
        """
        html = '<p>'
        for room in administrator.rooms.all():
            html += '%s<br>' % room.name
        html += '</p>'
        return format_html(mark_safe(html))
    list_rooms.short_description = 'salles administrées'


class MailAdmin(admin.ModelAdmin):
    """
    Admin configuration for Mail model
    """
    list_display = ('subject', 'sender', 'moderated', 'moderated_by', 'date')
    list_filter = ('moderated', 'date')
    search_fields = ('subject', 'sender', 'content',)


admin.site.register(Room, RoomAdmin)
admin.site.register(RoomBooking, RoomBookingAdmin)
admin.site.register(RoomAdministrator, RoomAdministratorAdmin)
admin.site.register(Mail, MailAdmin)
