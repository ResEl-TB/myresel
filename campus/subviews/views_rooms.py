from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

import calendar, datetime, json
from campus.forms import RoomBookingForm
from campus.models import RoomBooking, Room
from fonctions.decorators import ae_required

def calendarView(request, room='all', year=timezone.now().year, month=timezone.now().month, day='all'):
    """ View to display the month calendar of all events """

    # Slight hack to convert string paremeters in good format
    year = int(year)
    month = int(month)

    # Building calendar with events
    calendar.setfirstweekday(calendar.MONDAY)
    cal = list()
    if room != 'all':
        room = Room.objects.get(pk=int(room))
        if room.private:
            if request.user.is_authenticated():
                if not request.user.username in room.allowed_members:
                    messages.error(request, _('Vous n\'avez pas accès à cette page'))
                    return HttpResponseRedirect(reverse('home'))
            else:
                messages.error(request, _('Vous devez être connecté pour accéder à cette page'))
                return HttpResponseRedirect(reverse('home'))

        events = room.roombooking_set.filter(
            start_time__year=year, 
            start_time__month=month
        )
    else:
        events = RoomBooking.objects.filter(
            displayable=True, 
            start_time__year=year,
            start_time__month=month,
        )
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
    private_rooms = Room.objects.filter(private=True, allowed_members__contains=request.user.username) \
                        if request.user.is_authenticated() else None
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
def bookView(request, booking=None):
    """ View to book a room """
    if booking:
        instance = get_object_or_404(RoomBooking, id=booking)
        form = RoomBookingForm(request.POST or None, user=request.ldap_user, instance=instance)
    else:
        form = RoomBookingForm(request.POST or None, user=request.ldap_user)
    if form.is_valid():
        form.save()
        return render(request, 'campus/rooms/booking_success.html')
    return render(request, 'campus/rooms/booking.html', {'form': form})