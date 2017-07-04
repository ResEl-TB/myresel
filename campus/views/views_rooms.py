# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q

import calendar, datetime, json

from django.views.generic import DetailView
from django.views.generic import FormView

from campus.forms import RoomBookingForm, AddRoomForm
from campus.models import RoomBooking, Room, StudentOrganisation
from fonctions.decorators import ae_required

class UserNotAuthenticatedException(Exception):
    pass

class NotAllowedException(Exception):
    pass


# Linting disabled because it wrongly guess that room is always a str
# noinspection PyUnresolvedReferences
# pylint: disable=no-member
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
        if not request.user.is_authenticated():
            raise UserNotAuthenticatedException(_('Vous devez être connecté pour accéder à cette page'))

        if not room.user_can_access(request.ldap_user):
            raise NotAllowedException(_('Vous n\'avez pas accès à cette page'))

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

    if room != 'all':
        room = Room.objects.get(pk=int(room))
    try:
        q = construct_query(request, start_date, end_date, room)
    except (UserNotAuthenticatedException, NotAllowedException) as e :
        messages.error(request, e)
        return HttpResponseRedirect(reverse('campus:home'))
    events = RoomBooking.objects.filter(q)

    single_events = []

    for event in events:
        for occ in event.get_occurences():
            single_events.append((occ, event))

    # calendar date limits
    # TODO: show events that last multiple days
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
        'current_day_nbr': str(timezone.now().day)
    }

    return render(
        request,
        'campus/rooms/calendar.html',
        context,
    )

class AddRoom(FormView):
    """
    View to create a room
    """

    template_name = 'campus/rooms/room_form.html'
    success_url = reverse_lazy('campus:rooms:calendar')
    form_class = AddRoomForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AddRoom, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Opération réussie'))
        return super(AddRoom, self).form_valid(form)



class BookingView(FormView):
    """
    View to book an event or edit an event
    """
    template_name = 'campus/rooms/booking.html'
    success_url = reverse_lazy('campus:rooms:calendar')
    form_class = RoomBookingForm

    @method_decorator(login_required)
    #@method_decorator(ae_required) #CHANGE ME CHANGE ME CHANGE ME
    def dispatch(self, request, *args, **kwargs):
        self.booking = None
        if self.kwargs.get('booking', None):
            self.booking = RoomBooking.objects.get(id=self.kwargs['booking'])
            if not self.booking.user_can_manage(self.request.ldap_user):
                messages.error(self.request, _('Vous ne pouvez pas modifier cette réservation'))
                return HttpResponseRedirect(reverse('campus:rooms:calendar'))
        return super(BookingView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.POST or None, user=self.request.ldap_user, instance=self.booking)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Opération réussie'))
        return super(BookingView, self).form_valid(form)

class BookingDetailView(DetailView):
    model = RoomBooking
    template_name = 'campus/rooms/booking_detail.html'
    slug_field = "pk"
