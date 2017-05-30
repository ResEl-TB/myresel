from django import forms
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.core.exceptions import ValidationError
from django.forms import ModelForm, CharField, TextInput, Form, Textarea, ChoiceField, EmailField, IntegerField
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

    type = ChoiceField(
        widget=forms.Select(attrs={
            'class':'form-control',
            'id':'type',
        }),
        choices=ORGA_TYPE,
        label=_("Sélectionner ce que vous souhaitez créer"),
    )

    name = CharField(  # orgaName
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom"),
        }),
        validators=[MaxLengthValidator(50)],
        label=_("Nom"),
    )

    cn = CharField(  # cn
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom court; ex: tennis pour les Club tennis"),
        }),
        validators=[MaxLengthValidator(50)],
        label=_("Nom court"),
    )

    description = CharField(  # description
        widget=Textarea(attrs={
            'class': 'form-control',
            'placeholder': _("Présentation du l'organisation"),
            'rows': 5
        }),
        validators=[MaxLengthValidator(50)],
        label=_("Description"),
    )

    logo = forms.ImageField( #logo
        widget = forms.ClearableFileInput(),
        label = 'Logo',
        required = False,

    )

    email = EmailField(   # mlist
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Adresse de la mailing liste "),
        }),
        validators=[MaxLengthValidator(50)],
        label=_('Mailing liste'),
        required=False,
    )

    website = CharField(  # Website (if not a ResEl website)
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Site web"),
        }),
        validators=[MaxLengthValidator(50)],
        required=False,
    )

    campagneYear = forms.IntegerField( # Année de campagne
        min_value=1997,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("Année de campagne"),
        }),
        label=_('Année de Campagne'),
        required=False,
    )

    def clean_type(self):
        type = self.cleaned_data['type']
        if type not in [o[0] for o in self.ORGA_TYPE]:
            raise ValidationError(message=_("Merci de sélectionner un choix valide"), code="BAD TYPE")
        return (type)

    def clean_cn(self):
        cn = self.cleaned_data['cn'].lower()
        if StudentOrganisation.filter(cn=cn):
            raise ValidationError(_("Ce nom existe déjà, assurez vous de créer un club/asso qui n'existe pas déjà"), code="CN EXISTS")
        elif not re.match(r'^[a-z0-9-]+$', cn):
            raise ValidationError(message=_("Le nom court ne doit pas contenir d'espace est n'est contitué que de lettres et de chiffres"))
        return(cn)

    def clean_logo(self):
        logo = self.cleaned_data['logo']
        if self.cleaned_data['type'] != 'CLUB' and logo == None:
            raise ValidationError(message=_("Merci de renseigner un logo pour votre association/liste"), code="NO LOGO")
        return(logo)

    def clean_website(self):
        website = self.cleaned_data['website'].lower()
        if not re.match(r'^(http(s)*:\/\/)*[a-z0-9.-]+\.[a-z0-9]+$', website) and website != "":
            raise ValidationError(message=_("Veuillez rentrer une adresse web valide"), code="BAD WEBSITE")
        return(website)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not re.match(r'^[a-z1-9-_.+]+\@[a-z1-9-]+\.[a-z0-9-]+$', email) and email != "":
            raise ValidationError(message=_("Veuillez rentrer une adresse mail valide"), code="BAD MAIL")
        return(email)

    def clean_campagneYear(self):
        year = self.cleaned_data['campagneYear']
        if self.cleaned_data['type'] == "LIST" and year == None:
            raise ValidationError(_("Veuillez entrer une année de campagne valide"), code="WRONG YEAR")
        return(year)

    def clean(self):
        cleaned_data = super(ClubManagementForm, self).clean()

    def create_club(self):
        new_club = StudentOrganisation()
        new_club.name = self.cleaned_data['name']
        new_club.cn = self.cleaned_data['cn']
        new_club.email = self.cleaned_data['email']
        new_club.website = self.cleaned_data['website']
        if self.cleaned_data["logo"] != None:
            new_club.logo = self.cleaned_data["logo"]
        new_club.memebers = []
        new_club.prezs = []
        if new_club.email != '':
            new_club.ml_infos = True
        else:
            new_club.ml_infos = False
        new_club.description = self.cleaned_data['description']
        new_club.object_classes = ["studentOrganisation"]
        if self.cleaned_data['type'] == "CLUB":
            new_club.object_classes += ["tbClub"]
        elif self.cleaned_data['type'] == "ASSOS":
            new_club.object_classes += ["tbAsso"]
        elif self.cleaned_data['type'] == "LIST":
            new_club.object_classes += ["tbCampagne"]
            new_club.campagneYear = self.cleaned_data['campagneYear']
        new_club.save()

class ClubEditionForm(ClubManagementForm):

    def clean_cn(self):
        return(self.cleaned_data['cn'].lower())

    def clean_logo(self):
        logo = self.cleaned_data['logo']
        return(logo)
    def edit_club(self, pk):
        club = StudentOrganisation.get(cn=pk)
        club.name = self.cleaned_data['name']
        club.description = self.cleaned_data['description']
        club.email = self.cleaned_data['email']
        club.website = self.cleaned_data['website']
        if self.cleaned_data["logo"] != None:
            club.logo = self.cleaned_data["logo"]
        club.save()



class MajPersonnalInfo(PersonnalInfoForm):
    CAMPUS = [('Brest', "Brest"), ('Rennes', 'Rennes'), ('None', _('Je n\'habite pas à la Maisel'))]
    BUILDINGS_BREST = [('I%d' % i, 'I%d' % i) for i in range(1, 13)]
    BUILDINGS_RENNES = [('S1', 'Studios'), ('C1', 'Chambres')]

    BUILDINGS = [(0, _("Sélectionnez un Bâtiment"))]
    BUILDINGS += BUILDINGS_BREST
    BUILDINGS += BUILDINGS_RENNES

    photo = forms.ImageField(
        widget = forms.ClearableFileInput(),
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
        input_formats = [
            '%Y-%m-%d',      # '2006-10-25'
            '%d/%m/%Y',      # '10/25/2006'
            '%d/%m/%y'
        ]
    )

    certify_truth = forms.BooleanField(
        required = False
    )

class SearchSomeone(forms.Form):

    search_keys = ['first_name', 'last_name', 'mail', 'promo']

    what = forms.CharField(
        widget = forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Votre recherche')
        }),
    )

    strict = forms.BooleanField(
        widget = forms.CheckboxInput(),
        label = _('Recherche stricte'),
        label_suffix = _(''),
        required = False,
    )

    def clean_what(self):
        what = self.cleaned_data['what']
        return what.lower().strip()

    def _search_single_word(self, word, strict=False):
        """ Search in the ldap for users according to the key `search_keys`"""
        search_keys = self.search_keys
        if not strict:
            search_keys = map(lambda k: k + '__contains', search_keys)

        results = []
        for key in search_keys:
            results += LdapUser.filter(**{key: word})
        return results

    @staticmethod
    def int_safe(u):
        try:
            return int(u)
        except ValueError:
            return 0

    def _sort_results(self, unsorted):
        """ Sort results by promotion and by relevance """
        # Delete duplicates
        results = []
        for r in unsorted:
           if r not in [u.uid for u in results]:
               results.append(r)
        for result in results:
            result.promo = self.int_safe(result.promo)
        results.sort(key=lambda u: u.promo, reverse=True)
        return results

    def get_results(self, what, strict):
        results = []
        names = what.split()
        for name in names:
            results += self._search_single_word(name, strict)
        return self._sort_results(results)
