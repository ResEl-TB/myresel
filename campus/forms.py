from django import forms
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.core.exceptions import ValidationError
from django.forms import ModelForm, CharField, TextInput, Form
from django.forms.models import ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from campus.models import RoomBooking, Room, RoomAdmin, StudentOrganisation, Mail
from gestion_personnes.models import LdapUser
from gestion_personnes.forms import PersonnalInfoForm

from ldap3 import LDAPException
from fonctions import ldap

import datetime
import re

class RoomBookingForm(ModelForm):
    class Meta:
        model = RoomBooking
        fields = ("room", "description", "start_time", "end_time", "user", "booking_type", "displayable",
                  "recurring_rule", "end_recurring_period",)

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


class DisabledCharField(CharField):
    def __init__(self, disabled=True, *args, **kwargs):
        super(DisabledCharField, self).__init__(disabled=True, *args, **kwargs)

class SendMailForm(ModelForm):
    class Meta:
        model = Mail
        fields = ("sender", "subject", "content")
        widgets = {'sender': TextInput(attrs={'readonly':'readonly', 'class': 'form-control'}),}
        field_classes = {'sender': DisabledCharField,}

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

class MajPersonnalInfo(PersonnalInfoForm):
    CAMPUS = [('Brest', "Brest"), ('Rennes', 'Rennes'), ('None', _('Je n\'habite pas à la Maisel'))]
    BUILDINGS_BREST = [('I%d' % i, 'I%d' % i) for i in range(1, 13)]
    BUILDINGS_RENNES = [('S1', 'Studios'), ('C1', 'Chambres')]

    BUILDINGS = [(0, _("Sélectionnez un Bâtiment"))]
    BUILDINGS += BUILDINGS_BREST
    BUILDINGS += BUILDINGS_RENNES

    photo = forms.ImageField(
        widget = forms.ClearableFileInput({
            'class' : 'form-control'
        }),
        label = 'Photo',
        label_suffix = _(''),
        required = False,

    )

    remove_photo = forms.BooleanField(
        widget = forms.CheckboxInput(),
        label = _("Supprimer ma photo"),
        label_suffix = _(''),
        required = False,
    )

    is_public = forms.BooleanField(
        widget = forms.CheckboxInput(),
        label = _("Rendre publiques les details de mon profil"),
        label_suffix = _(''),
        initial = False,
        required = False,
    )

    birth_date = forms.DateField(
        widget = forms.DateInput(attrs={
            'class' : 'form-control',
            'id' : 'datePicker'
        }),
        required = False,
    )

    certify_truth = forms.BooleanField(
        required = False
    )

class SearchSomeone(forms.Form):

    what = forms.CharField(
        widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('ex: Siffredi')
        }),
    )

    is_approx = forms.BooleanField(
        widget = forms.CheckboxInput(),
        label = _('Recherche approximative'),
        label_suffix = _(''),
        required = False,
    )

    def getResult(self, what, is_approx):
        what = what.strip()

        if re.match(r'^[a-z1-9-_.+]+\@[a-z1-9-]+\.[a-z0-9-]+$', what.lower()):
            return LdapUser.filter(mail=what)

        elif "@" in what and is_approx == True:
            return LdapUser.filter(mail__contains=what)

        elif re.match(r'^[a-z- ]+ ([a-z-]+)', what.lower()):

            try:
                elList = what.split(' ')
                name1, name2 = elList[0], elList[-1]
                if is_approx == True:
                    res = LdapUser.filter(first_name__contains=name1)
                    res += LdapUser.filter(first_name__contains=name2)
                    res += LdapUser.filter(last_name__contains=name1)
                    res += LdapUser.filter(last_name__contains=name2)
                else:
                    res = LdapUser.filter(first_name=name1)
                    res += LdapUser.filter(first_name=name2)
                    res += LdapUser.filter(last_name=name1)
                    res += LdapUser.filter(last_name=name2)
                return list(dict((obj.first_name, obj) for obj in res).values()) #exludes duplicates

            except LDAPException as e:
                return False
            except Exception as e:
                return False

        elif re.match(r'^[a-z-]+', what.lower()):
            try:
                if is_approx == True:
                    res = LdapUser.filter(first_name__contains=what)
                    res += LdapUser.filter(last_name__contains=what)
                else:
                    res = LdapUser.filter(first_name=what)
                    res += LdapUser.filter(last_name=what)
                return(res)

            except LDAPException as e:
                return False
            except Exception as e:
                return False

        return False

    def clean(self):
        cleaned_data = super(SearchSomeone, self).clean()
