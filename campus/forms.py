from django import forms
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms import ModelForm, CharField, TextInput, Form, Textarea, ChoiceField,\
                                    EmailField, IntegerField, Select, CheckboxInput, SelectMultiple
from django.forms.models import ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from campus.models import RoomBooking, Room, RoomAdmin, StudentOrganisation, Mail, Association, ListeCampagne
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
        if user: #Otherwise the test crashes
            self.user = user
            if not RoomAdmin.objects.filter(user__username=user.uid):
                del self.fields['user']
                clubs = StudentOrganisation.filter(members__contains='uid=%s' % user.uid)
                queryset = Q(private=False)
                for club in clubs:
                    queryset |= Q(private=True, clubs__contains=club.cn)
                self.fields['room'] = ModelMultipleChoiceField(
                    queryset=Room.objects.filter(queryset),
                    widget=SelectMultiple(attrs={'class': 'form-control'})
                )
        else:
            del self.fields['user']
            self.user = None

    def save(self, commit=True, *args, **kwargs):
        m = super(RoomBookingForm, self).save(commit=False, *args, **kwargs)

        if m.booking_type == 'hidden':
            m.displayable = False

        if 'user' in self.fields:
            m.user = self.cleaned_data['user']
        else:
            m.user = self.user.uid

        m.save()

        #piano, created = Room.objects.get_or_create(
        #    name='Salle piano',
        #    defaults={'location': 'F', 'private': True},
        #)
        #meeting, created = Room.objects.get_or_create(
        #    name='Salle réunion',
        #    defaults={'location': 'F', 'private': False},
        #)

        #pr = False    # Detects is the piano or réunion room is selected
        #rooms = []
        #for room in self.cleaned_data['room']:
        #    if 'piano' in room.name.lower() or 'réunion' in room.name.lower():
        #        pr = True
        #    else:
        #        rooms.append(room)
        #
        #if m.pk:
        #    m.room.clear()
        #
        #if pr:
        #    m.room.add(piano)
        #    m.room.add(meeting)
        #for room in rooms:
        #    m.room.add(room)
        m.room = self.cleaned_data['room']
        m.notify_mailing_list()
        return m


    def clean(self):
        cleaned_data = super(RoomBookingForm, self).clean()
        start_time = cleaned_data.get('start_time', None)
        end_time = cleaned_data.get('end_time', None)
        recurring_rule = cleaned_data.get('recurring_rule', None)
        rooms = cleaned_data.get('room', None)

        # DAT HACK
        #piano, created = Room.objects.get_or_create(
        #    name='Salle piano',
        #    defaults={'location': 'F', 'private': True},
        #)
        #meeting, created = Room.objects.get_or_create(
        #    name='Salle réunion',
        #    defaults={'location': 'F', 'private': False},
        #)

        # Deactivated because it is possible to add past events for record
        # if start_time < datetime.datetime.now():
        #     self.add_error('start_time', _('La date de début est antérieure à aujourd\'hui'))

        #If a user disable JS, he can send empty fields
        if end_time and start_time:
            if end_time < start_time:
                self.add_error('end_time', _('La date de fin est avant la date de début de l\'évènement'))

        if recurring_rule != "NONE" and not cleaned_data.get('end_recurring_period', None):
            self.add_error('end_recurring_period', _('La date de fin de la récurrence est invalide'))

        if rooms and self.user:
            for room in rooms:
                if not room.user_can_access(self.user):
                    self.add_error('room', _("Vous ne pouvez pas gérer cette salle"))
        elif rooms: #Needed for testing purpose, otherwise it crashes
            for room in rooms:
                if room.private:
                    self.add_error('room', _("Vous ne pouvez pas gérer cette salle"))


        # Deactivated because why hu ??
        # if start_time.date() != end_time.date():
        #     self.add_error('end_time', _('Vous ne pouvez réserver sur plusieurs jours'))

        # Check if room are available
        #for room in cleaned_data['room']:
        #    # DAT HACK BIS
        #    if 'piano' in room.name.lower() or 'réunion' in room.name.lower():
        #        if not piano.is_free(start_time, end_time) or \
        #                not meeting.is_free(start_time, end_time):
        #            self.add_error('room', _("La salle %s n'est pas disponible") % room)
        #    elif not room.is_free(start_time, end_time):
        #        self.add_error('room', _("La salle %s n'est pas disponible") % room)
        return self.cleaned_data

class AddRoomForm(ModelForm):
    class Meta:
        model = Room
        fields = ("location", "name", "mailing_list", "private", "clubs")
        widgets = {
            'location': Select(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'mailing_list': TextInput(attrs={'class': 'form-control'}),
            'private': CheckboxInput(attrs={'class': 'form-check-input'}),
            'clubs': TextInput(attrs={'class': 'form-control form-control-warning', 'id': 'clubs_area'}),
        }

    def clean_mailing_list(self):
        email=self.cleaned_data["mailing_list"]
        if not (re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', email) or email == ""):
            raise ValidationError(message=_("L'adresse email semble être invalide"), code="Bad MAIL")
        return(email)

    def clean_clubs(self):
        clubs = ""
        if self.cleaned_data["clubs"] != '':
            clubs = list(set(self.cleaned_data["clubs"].split(";"))) #deletes duplicates
            for club in clubs:
                try:
                    StudentOrganisation.get(cn=club)
                except ObjectDoesNotExist:
                    raise ValidationError(message=_("Le club suivant n'existe pas: %s"%(club,)), code="CLUB DOES NOT EXIST")
                if not re.match(r'^[a-z0-9-]+', club):
                    raise ValidationError(message=_("Le club suivant n'est pas un nom valide: %s"%(club,)), code="BAD CLUB")
        return(";".join(clubs))


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
        validators=[MaxLengthValidator(1200)],
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

        #If we don't do this we get an error cuz our LDAP scheme does not allow
        # a single model for each type of organisation
        if self.cleaned_data['type'] == "CLUB":
            new_club = StudentOrganisation()
            new_club.object_classes = ["tbClub"]
        elif self.cleaned_data['type'] == "ASSOS":
            new_club = Association()
            new_club.object_classes = ["tbAsso"]
        elif self.cleaned_data['type'] == "LIST":
            new_club = ListeCampagne()
            new_club.object_classes = ["tbCampagne"]
            new_club.campagneYear = self.cleaned_data['campagneYear']

        new_club.name = self.cleaned_data['name']
        new_club.cn = self.cleaned_data['cn']
        new_club.website = self.cleaned_data['website']
        new_club.description = self.cleaned_data['description']
        new_club.object_classes = ["studentOrganisation"]
        new_club.memebers = []
        new_club.prezs = []

        if self.cleaned_data["logo"] != None:
            new_club.logo = self.cleaned_data["logo"]

        new_club.email = self.cleaned_data['email']
        if new_club.email != '':
            new_club.ml_infos = True
        else:
            new_club.ml_infos = False

        new_club.save()

class ClubEditionForm(ClubManagementForm):

    def clean_cn(self):
        return(self.cleaned_data['cn'].lower())

    def clean_logo(self):
        logo = self.cleaned_data['logo']
        return(logo)
    def edit_club(self, pk):
        club = StudentOrganisation.get(cn=pk)

        #If we don't do this we get an error cuz our LDAP scheme does not allow
        # a single model for each type of organisation
        if "tbCampagne" in club.object_classes:
            club=ListeCampagne.get(cn=pk)
        elif "tbAsso" in club.object_classes:
            club=Association.get(cn=pk)

        club.name = self.cleaned_data['name']
        club.description = self.cleaned_data['description']
        club.website = self.cleaned_data['website']

        club.email = self.cleaned_data['email']
        if club.email != '':
            club.ml_infos = True
        else:
            club.ml_infos = False

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
        label_suffix = '',
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
        label_suffix = '',
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
        label_suffix = '',
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
