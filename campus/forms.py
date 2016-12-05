from django.forms import ModelForm

from campus.models import RoomBooking

class RoomBookingForm(ModelForm):
    class META:
        model = RoomBooking
        fields = '__all__'