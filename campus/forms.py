from django.core.validators import MaxLengthValidator
from django.forms import ModelForm, CharField, TextInput, Form
from django.forms.models import ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from campus.models import RoomBooking, Room, RoomAdmin, StudentOrganisation, Mail
import datetime

class RoomBookingForm(ModelForm):
    class Meta:
        model = RoomBooking
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RoomBookingForm, self).__init__(*args, **kwargs)

        # Display the rooms the user is allowed to book
        self.user = user.uid
        if not RoomAdmin.objects.filter(user__username=user.uid):
            del self.fields['user']
            clubs = StudentOrganisation.filter(members__contains='uid=%s' % user.uid)
            queryset = Q(private=False)
            for club in clubs:
                queryset |= Q(private=True, clubs__contains=club.cn)
            self.fields['room'] = ModelMultipleChoiceField(
                queryset=Room.objects.filter(queryset)
            )

    def save(self, commit=True, *args, **kwargs):
        m = super(RoomBookingForm, self).save(commit=False, *args, **kwargs)

        if m.booking_type == 'hidden':
            m.displayable = False

        if 'user' in self.fields:
            m.user = self.cleaned_data['user']
        else:
            m.user = self.user

        m.save()

        piano, created = Room.objects.get_or_create(
            name='Salle piano',
            defaults={'location': 'F', 'private': True},
        )
        meeting, created = Room.objects.get_or_create(
            name='Salle réunion',
            defaults={'location': 'F', 'private': False},
        )

        pr = False    # Detects is the piano or réunion room is selected
        rooms = []
        for room in self.cleaned_data['room']:
            if 'piano' in room.name.lower() or 'réunion' in room.name.lower():
                pr = True
            else:
                rooms.append(room)

        if m.pk:
            m.room.clear()

        if pr:
            m.room.add(piano)
            m.room.add(meeting)
        for room in rooms:
            m.room.add(room)
        m.notify_mailing_list()
        return m


    def clean(self):
        cleaned_data = super(RoomBookingForm, self).clean()
        start_time = cleaned_data['start_time']
        end_time = cleaned_data['end_time']

        # DAT HACK
        piano, created = Room.objects.get_or_create(
            name='Salle piano',
            defaults={'location': 'F', 'private': True},
        )
        meeting, created = Room.objects.get_or_create(
            name='Salle réunion',
            defaults={'location': 'F', 'private': False},
        )

        # Deactivated because it is possible to add past events for record
        # if start_time < datetime.datetime.now():
        #     self.add_error('start_time', _('La date de début est antérieure à aujourd\'hui'))

        if end_time < start_time:
            self.add_error('end_time', _('La date de fin est avant la date de début de l\'évènement'))

        # Deactivated because why hu ??
        # if start_time.date() != end_time.date():
        #     self.add_error('end_time', _('Vous ne pouvez réserver sur plusieurs jours'))

        # Check if room are available
        for room in cleaned_data['room']:
            # DAT HACK BIS
            if 'piano' in room.name.lower() or 'réunion' in room.name.lower():
                if not piano.is_free(start_time, end_time) or \
                        not meeting.is_free(start_time, end_time):
                    self.add_error('room', _("La salle %s n'est pas disponible") % room)
            elif not room.is_free(start_time, end_time):
                self.add_error('room', _("La salle %s n'est pas disponible") % room)

class SendMailForm(ModelForm):
    class Meta:
        model = Mail
        fields = '__all__'
        widgets = {
            'sender': TextInput(attrs={'readonly':'readonly', 'class': 'form-control'}),
        }

class ClubManagementForm(Form):

    ORGA_TYPE = [
        ("CLUB", "Club"),
        ("ASSOS", "Association"),
        ("LIST", "Liste de campagne"),
    ]

    name = CharField(  # orgaName
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom du club"),
        }),
        validators=[MaxLengthValidator(50)],
    )

    cn = CharField(  # cn
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom court"),
        }),
        validators=[MaxLengthValidator(50)],
    )

    description = CharField(  # description
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Présentation "),
        }),
        validators=[MaxLengthValidator(50)],
    )

    logo = CharField(  # deduced from the cn
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("lien vers le logo"),
        }),
        validators=[MaxLengthValidator(50)],
    )

    email = CharField(   # mlist
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Mailing liste "),
        }),
        validators=[MaxLengthValidator(50)],
    )

    website = CharField(  # Website (if not a ResEl website)
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Site web de contact"),
        }),
        validators=[MaxLengthValidator(50)],
    )
