from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from campus.forms import RoomBookingForm
from campus.models import RoomBooking, Room

def BookRoomView(request):
    if request.method == 'POST':
        form = RoomBookingForm(request.POST)
        if form.is_valid():
            free = True   # Detects if all the rooms are free
            pr = False    # Detects is the piano or réunion room is selected
            rooms = []
            for value in form.cleaned_data['room']:
                room = Room.objects.get(pk=value)

                if 'piano' in room.name.lower() or 'réunion' in room.name.lower():
                    pr = True
                    if not Room.objects.get(name='piano').is_free(form.cleaned_data['start_time'], form.cleaned_data['end_time']) or \
                        not Room.objects.get(name='réunion').is_free(form.cleaned_data['start_time'], form.cleaned_data['end_time']):
                        free = False
                        messages.error(request, _('Une des salles n\'est pas libre'))
                        break
                elif not room.is_free(form.cleaned_data['start_time'], form.cleaned_data['end_time']):
                    free = False
                    messages.error(request, _('Une des salles n\'est pas libre'))
                    break
                else:
                    rooms.append(room)

            if free:
                booking = RoomBooking()
                booking.name = form.cleaned_data['name']
                booking.description = form.cleaned_data['description']
                booking.start_time = form.cleaned_data['start_time']
                booking.end_time = form.cleaned_data['end_time']
                booking.user = request.user.username
                booking.booking_type = form.cleaned_data['booking_type']
                if booking.booking_type == 'hidden':
                    booking.displayable = False
                booking.save()
                if pr:
                    booking.room.add(Room.objects.get(name='piano'))
                    booking.room.add(Room.objects.get(name='réunion'))
                for room in rooms:
                    booking.room.add(room)
                booking.notify_mailing_list()
                booking.notify_moderators()
                return render(request, 'campus/booking_success.html')

    else:
        form = RoomBookingForm()

    return render(request, 'campus/booking.html', {'form': form})