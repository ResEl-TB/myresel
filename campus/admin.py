from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from campus.models import Room, RoomBooking, RoomAdmin, Mail, MailModerator

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

admin.site.register(Room)
admin.site.register(RoomBooking, RoomBookingAdmin)
admin.site.register(RoomAdmin)

admin.site.register(Mail)
admin.site.register(MailModerator)