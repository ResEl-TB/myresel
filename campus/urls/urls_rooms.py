from django.conf.urls import url

from campus.views import BookingView, calendar_view, BookingDetailView, AddRoom,\
                         RequestAvailability, ManageRooms, DeleteRoom, DeleteBooking

app_name = 'campus_rooms'

urlpatterns = [
    url(r'^$', calendar_view, name='calendar'),
    url(r'^(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/$', calendar_view, name='calendar-month'),
    url(r'^(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/(?P<day>([0-9])|([1-2][0-9])|(3[0-1]))/$', calendar_view, name='calendar-day'),
    url(r'^(?P<room>[0-9]+)/$', calendar_view, name='calendar-room'),
    url(r'^(?P<room>[0-9]+)/(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/$', calendar_view, name='calendar-room-month'),
    url(r'^(?P<room>[0-9]+)/(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/(?P<day>([0-9])|([1-2][0-9])|(3[0-1]))/$', calendar_view, name='calendar-room-day'),

    url(r'^réservation$', BookingView.as_view(), name='booking'),
    url(r'^modification/(?P<booking>[0-9]+)/$', BookingView.as_view(), name='mod-booking'),
    url(r'^event/(?P<slug>[0-9]+)/$', BookingDetailView.as_view(), name='booking-detail'),
    url(r'^delete-booking/(?P<pk>[0-9]+)$', DeleteBooking.as_view(), name="delete-booking"),
    url(r'^check', RequestAvailability.as_view(), name="check-availability"),

    url(r'^add-room$', AddRoom.as_view(), name="add-room"),
    url(r'^edit-room/(?P<room>[0-9]+)$', AddRoom.as_view(), name="edit-room"),
    url(r'^manage-rooms$', ManageRooms.as_view(), name="manage-rooms"),
    url(r'^delete-room/(?P<pk>[0-9]+)$', DeleteRoom.as_view(), name="delete-room"),
]
