from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from campus.models import Room, RoomBooking, RoomAdmin, Mail, StudentOrganisation

class RoomBookingAdmin(admin.ModelAdmin):
    list_display = ('description', 'user', 'start_time', 'end_time', 'list_rooms')
    list_filter = ('room', 'start_time', 'end_time')
    search_fields = ('user',)

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

class Room_admin(admin.ModelAdmin):
    list_display = ('name', 'location', 'private', 'list_clubs')
    list_filter = ('location', 'private')
    search_fields = ('name',)

    def list_clubs(self, room):
        """
        List all the clubs allowed to access the room
        """
        
        html = '<p>'
        for club in room.get_clubs():
            html += '%s<br>' % club
        html += '</p>'
        return format_html(mark_safe(html))
    list_clubs.short_description = 'clubs autorisés'

class RoomAdmin_admin(admin.ModelAdmin):
    list_display = ('user', 'list_rooms')

    def list_rooms(self, admin):
        """
        List all the rooms of the given booking
        """
        html = '<p>'
        for room in admin.rooms.all():
            html += '%s<br>' % room.name
        html += '</p>'
        return format_html(mark_safe(html))
    list_rooms.short_description = 'salles administrées'

admin.site.register(Room, Room_admin)
admin.site.register(RoomBooking, RoomBookingAdmin)
admin.site.register(RoomAdmin, RoomAdmin_admin)

admin.site.register(Mail)