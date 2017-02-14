# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
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


def construct_query(request, start_date, end_date, room='all'):
    """
    Construct a query to get all the events between 2 dates
    and in specific rooms

    :param request:
    :param start_date:
    :param end_date:
    :param room:
    :return:
    """
    q_rooms = Q()
    if room == 'all':
        q_rooms = Q()
    else:
        room = Room.objects.get(pk=int(room))
        if not request.user.is_authenticated():
            messages.error(request, _('Vous devez être connecté pour accéder à cette page'))
            return HttpResponseRedirect(reverse('home'))

        if not room.user_can_access(request.ldap_user):
            messages.error(request, _('Vous n\'avez pas accès à cette page'))
            return HttpResponseRedirect(reverse('home'))

        q_rooms &= Q(room__id=room.pk)

    q_dates_start_in = Q(
        start_time__gte=start_date,
        start_time__lt=end_date
    )

    q_dates_end_in = Q(
        end_time__gte=start_date,
        end_time__lt=end_date
    )

    q_recc_end = Q(
        start_time__gte=start_date,
        end_recurring_period__gte=end_date,
    ) & (Q(recurring_rule='DAILY') | Q(recurring_rule='WEEKLY') | Q(recurring_rule='MONTHLY'))

    return q_rooms & (q_dates_start_in | q_dates_end_in | q_recc_end)

def calendar_view(request, room='all', year=timezone.now().year, month=timezone.now().month, day='all'):
    """ View to display the month calendar of all events """

    # Slight hack to convert string parameters in good format
    year = int(year)
    month = int(month)

    # TODO: renormalize for missing day month ?
    # Show either the whole month or a single day
    if day == 'all':
        day = -1
        start_date = datetime.datetime(year=year, month=month, day=1)
        end_date = start_date + relativedelta(months=+1)

    else:
        day = int(day)
        start_date = datetime.datetime(year=year, month=month, day=day)
        end_date = start_date + relativedelta(days=+1)

    # Building calendar with events
    calendar.setfirstweekday(calendar.MONDAY)
    cal = list()

    q = construct_query(request, start_date, end_date, room)
    events = RoomBooking.objects.filter(q)

    single_events = []

    for event in events:
        for occ in event.get_occurences():
            single_events.append((occ, event))

    # calendar date limits
    if day > 0:  # Show a single day
        day = int(day)
        current_date = datetime.date(year=year, month=month, day=day)

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
                        (datetime.date(year=year, month=month, day=day), [e[1] for e in single_events if e[0].day == day])
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