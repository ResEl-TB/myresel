from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Q

import calendar, datetime, json
from campus.forms import RoomBookingForm
from campus.models import RoomBooking, Room, StudentOrganisation
from fonctions.decorators import ae_required

def calendar_view(request, room='all', year=timezone.now().year, month=timezone.now().month, day='all'):
    """ View to display the month calendar of all events """

    # Slight hack to convert string parameters in good format
    year = int(year)
    month = int(month)

    # Building calendar with events
    calendar.setfirstweekday(calendar.MONDAY)
    cal = list()

    # View the calendar for a specific room
    if room != 'all':
        room = Room.objects.get(pk=int(room))

        if not request.user.is_authenticated():
            messages.error(request, _('Vous devez être connecté pour accéder à cette page'))
            return HttpResponseRedirect(reverse('home'))

        if not room.user_can_access(request.ldap_user):
            messages.error(request, _('Vous n\'avez pas accès à cette page'))
            return HttpResponseRedirect(reverse('home'))

        # TODO: events that ends during the month also :/
        events = room.roombooking_set.filter(
            start_time__year=year, 
            start_time__month=month
        )
    else:
        # TODO: events that ends during the month also :/
        events = RoomBooking.objects.filter(
            displayable=True, 
            start_time__year=year,
            start_time__month=month,
        )

    # calendar date limits
    if day != 'all':
        day = int(day)
        current_date = datetime.date(year=year, month=month, day=day)
        events = events.filter(start_time__day=day)
        cal.append(
            [(datetime.date(year=year, month=month, day=day), events)]
        )
    else:
        current_date = datetime.date(year=year, month=month, day=15)
        # Show all weeks of month
        for week in calendar.monthcalendar(year, month):
            week_events = list()
            for day in week:
                if day == 0:
                    week_events.append(
                        (0, None)
                    )
                else:
                    week_events.append(
                        (datetime.date(year=year, month=month, day=day), [e for e in events if e.start_time.day == day])
                    )
            cal.append(week_events)

    # Getting all the rooms
    if request.user.is_authenticated():
        queryset = Q()
        for club in StudentOrganisation.filter(members__contains='uid=%s' % request.ldap_user.uid):
            queryset |= Q(clubs__contains=club.cn)
        private_rooms = Room.objects.filter(queryset)
    else:
        private_rooms = []
    rooms = [
        ('Salles clubs', private_rooms),
        ('Salles du foyer', Room.objects.filter(private=False, location='F')),
        ('Salles de l\'école', Room.objects.filter(private=False, location='S')),
        ('Autre', Room.objects.filter(private=False, location__in=['O', 'C'])),
    ]

    context = {
        'calendar': cal,
        'current_date': current_date,
        'rooms': rooms,
        'current_room': room,
    }

    return render(
        request, 
        'campus/rooms/calendar.html', 
        context,
    )

@login_required
@ae_required
def booking_view(request, booking=None):
    """ View to book a room """
    if booking:
        instance = get_object_or_404(RoomBooking, id=booking)
        granted = False
        for room in instance.room.all():
            if room.user_can_manage(request.ldap_user):
                # User can manage reservations for this room
                granted = True

        if request.ldap_user.uid == instance.user:
            # User can modify his own reservation
            granted = True

        if not granted:
            messages.error(request, _('Vous ne pouvez pas modifier cette réservation'))
            return HttpResponseRedirect(reverse('campus:rooms:calendar'))

        form = RoomBookingForm(request.POST or None, user=request.ldap_user, instance=instance)
    else:
        form = RoomBookingForm(request.POST or None, user=request.ldap_user)
    if form.is_valid():
        form.save()
        messages.success(request, _('Opération réussie'))
        return HttpResponseRedirect(reverse('campus:rooms:calendar'))
    return render(request, 'campus/rooms/booking.html', {'form': form})