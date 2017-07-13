# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http import Http404

import calendar, datetime, json, copy

from django.views.generic import DetailView, FormView, View, ListView, DeleteView, UpdateView

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

    q_dates_in = Q(
        start_time__lt=end_date,
        end_time__gte=start_date,
    )

    q_recc = Q(
        start_time__lt=end_date,
        end_recurring_period__gte=start_date,
    ) & (Q(recurring_rule='DAILY') | Q(recurring_rule='WEEKLY') | Q(recurring_rule='MONTHLY'))

    return q_rooms & (q_dates_in | q_recc)

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
            #Temporarily changes the start_date and end_date for each event
            #This is needed in order to properly display dates for recurrent event that last multiple days
            event = copy.deepcopy(event)
            event.start_time, event.end_time = occ[0], occ[1]
            single_events.append((occ, event))
    #We only need event that are from this month
    single_events = [e for e in single_events if (e[0][0].month == month and e[0][0].year == year) or (e[0][1].month == month and e[0][1].year == year)]

    # calendar date limits
    if day > 0:  # Show a single day
        day = int(day)
        current_date = datetime.date(year=year, month=month, day=day)
        cal.append(
            # Shows the day's event and also those that last multiple days
            [(datetime.date(year=year, month=month, day=day), [e[1] for e in single_events if e[0][0].day == day or (e[0][0].day < day and e[0][1].day >= day) ])]
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
                        (datetime.date(year=year, month=month, day=day), [e[1] for e in single_events if e[0][0].day == day or (e[0][0].day < day and e[0][1].day >= day)])
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
        'current_day': [str(timezone.now().day), str(timezone.now().month), str(timezone.now().year)]
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
    success_url = reverse_lazy('campus:rooms:manage-rooms')
    form_class = AddRoomForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(self.request, _("Vous n'avez pas accès à cette page"))
            return HttpResponseRedirect(reverse('campus:rooms:calendar'))
        return super(ManageRooms, self).dispatch(request, *args, **kwargs)
        self.room = None
        if self.kwargs.get('room', None):
            self.room = get_object_or_404(Room, id=self.kwargs["room"])
        return super(AddRoom, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class == None:
            form_class = self.get_form_class()
        return form_class(self.request.POST or None, instance=self.room)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _('Opération réussie'))
        return super(AddRoom, self).form_valid(form)

class ManageRooms(ListView):
    """
    View used to manage rooms
    """

    template_name = 'campus/rooms/room_management.html'
    model = Room

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(self.request, _("Vous n'avez pas accès à cette page"))
            return HttpResponseRedirect(reverse('campus:rooms:calendar'))
        return super(ManageRooms, self).dispatch(request, *args, **kwargs)

class DeleteRoom(DeleteView):
    """
    View used to remove a rooms
    """
    model = Room
    success_url = reverse_lazy('campus:rooms:manage-rooms')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(self.request, _("Vous n'avez pas accès à cette page"))
            return HttpResponseRedirect(reverse('campus:rooms:calendar'))
        return super(DeleteRoom, self).dispatch(request, *args, **kwargs)

class BookingView(FormView):
    """
    View to book an event or edit an event
    """
    template_name = 'campus/rooms/booking.html'
    success_url = reverse_lazy('campus:rooms:calendar')
    form_class = RoomBookingForm

    @method_decorator(login_required)
    #@method_decorator(ae_required) #TODO: CHANGE ME CHANGE ME CHANGE ME
    def dispatch(self, request, *args, **kwargs):
        self.booking = None
        if self.kwargs.get('booking', None):
            self.booking = get_object_or_404(RoomBooking, id=self.kwargs['booking'])
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

class DeleteBooking(DeleteView):
    """
    View used to delete a registered booking
    """
    model = RoomBooking
    success_url = reverse_lazy('campus:rooms:calendar')

    #TODO: RIGHTS
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(DeleteBooking, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        #TODO: Rights rights rights !!!
        return super(DeleteBooking, self).post(self, request, *args, **kwargs)


class RequestAvailability(View):
    """
    View that returns avaibility of a room to ajax requests
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(RequestAvailability, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.is_ajax:
            room_pk = request.GET.get('value', None)
            start = request.GET.get('start', None)
            end = request.GET.get('end', None)
            print(room_pk, start, end)
            if room_pk == None or start == None or end == None:
                raise Http404
            room = get_object_or_404(Room, pk=room_pk)
            answer = 0
            if not room.is_free(start, end):
                answer = room.name
            return HttpResponse(answer)
        else:
            raise Http404

class BookingDetailView(DetailView):
    model = RoomBooking
    template_name = 'campus/rooms/booking_detail.html'
    slug_field = "pk"
