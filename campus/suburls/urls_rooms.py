from django.conf.urls import url

from campus.views import bookingView, calendarView

urlpatterns = [
    url(r'^$', calendarView, name='calendar'),
    url(r'^(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/$', calendarView, name='calendar-month'),
    url(r'^(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/(?P<day>([0-9])|([1-2][0-9])|(3[0-1]))/$', calendarView, name='calendar-day'),
    url(r'^(?P<room>[0-9]+)/$', calendarView, name='calendar-room'),
    url(r'^(?P<room>[0-9]+)/(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/$', calendarView, name='calendar-room-month'),
    url(r'^(?P<room>[0-9]+)/(?P<year>(199[0-9])|(20[0-2][0-9]))/(?P<month>([0-9])|(1[0-2]))/(?P<day>([0-9])|([1-2][0-9])|(3[0-1]))/$', calendarView, name='calendar-room-day'),
    
    url(r'^réservation$', bookingView, name='booking'),
    url(r'^modification/(?P<booking>[0-9]+)/$', bookingView, name='mod-booking'),
]