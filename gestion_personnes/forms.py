# -*- coding: utf-8 -*-
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator, EmailValidator
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from fonctions.generic import current_year
from gestion_personnes.models import LdapUser, LdapOldUser

# TODO : merge personnal info form and Inscription form


class InvalidUID(Exception):
    pass


class PersonnalInfoForm(forms.Form):
    CAMPUS = [('Brest', "Brest"), ('Rennes', 'Rennes'), ('None', _('Je n\'habite pas à la Maisel'))]
    BUILDINGS_BREST = [('I%d' % i, 'I%d' % i) for i in range(1, 13)]
    BUILDINGS_RENNES = [('S1', 'Studios'), ('C1', 'Chambres')]

    BUILDINGS = [(0, _("Sélectionnez un Bâtiment"))]
    BUILDINGS += BUILDINGS_BREST
    BUILDINGS += BUILDINGS_RENNES

    FORMATIONS = [
        (0, _('Indiquez votre formation')),
        ('FIG', _('Ingénieur généraliste (FIG)')),
        ('FIP', _('Ingénieur par alternance (FIP)')),
        ('Master', _('Master spécialisé')),
        ('Autre', _('Autre'))
    ]

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse e-mail"),
        }),
    )

    campus = forms.ChoiceField(
        choices=CAMPUS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': _("Campus"),
        })
    )

    building = forms.ChoiceField(
        choices=BUILDINGS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': _("Bâtiment"),
        }),
    )

    room = forms.IntegerField(
        min_value=0,
        max_value=330,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("N° de Chambre"),
        }),
        required=False,
    )

    address = forms.CharField(
        max_length=512,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse postale complète"),
            'rows': '5'
        }),
        required=False,
    )

    phone = PhoneNumberField(
        widget=PhoneNumberField.widget(attrs={
            'class': 'form-control',
            'placeholder': _("Numéro de téléphone"),
        })
    )

    certify_truth = forms.BooleanField(
        label=_("Je certifie sur l'honneur que les informations saisies sont correctes."),
        widget=forms.CheckboxInput()
    )

    def clean_campus(self):
        campus = self.cleaned_data['campus']

        if campus == '0':
            raise ValidationError(message=_("Veuillez sélectionner un campus"), code="NO CAMPUS")
        return campus

    def clean_formation(self):
        formation = self.cleaned_data['formation']

        if formation == '0':
            raise ValidationError(message=_("Veuillez sélectionner une formation"), code="NO FORMATION")
        return formation

    def clean(self):
        cleaned_data = super(PersonnalInfoForm, self).clean()
        campus = cleaned_data.get("campus")
        building = cleaned_data.get("building")
        address = cleaned_data.get("address")
        room = cleaned_data.get("room")

        if (campus == "Brest" or campus == "Rennes") and room is None:
            self.add_error("room", _("Ce champ est obligatoire"))
        if campus == "Brest" and building not in [a[0] for a in self.BUILDINGS_BREST]:
            self.add_error('building', _("Veuillez choisir un bâtiment du campus de Brest"))
        if campus == "Rennes" and building not in [a[0] for a in self.BUILDINGS_RENNES]:
            self.add_error('building', _("Veuillez choisir un bâtiment du campus de Rennes"))
        if campus == "None" and address == "":
            self.add_error('address', _("Veuillez saisir votre addresse postale"))


class InscriptionForm(forms.Form):
    CAMPUS = [('Brest', "Brest"), ('Rennes', 'Rennes'), ('None', _('Je n\'habite pas à la Maisel'))]
    BUILDINGS_BREST = [('I%d' % i, 'I%d' % i) for i in range(1, 13)]
    BUILDINGS_RENNES = [('S1', 'Studios'), ('C1', 'Chambres')]

    BUILDINGS = [(0, _("Sélectionnez un Bâtiment"))]
    BUILDINGS += BUILDINGS_BREST
    BUILDINGS += BUILDINGS_RENNES

    FORMATIONS = [
        (0, _('Indiquez votre formation')),
        ('FIG', _('Ingénieur généraliste (FIG)')),
        ('FIP', _('Ingénieur par alternance (FIP)')),
        ('Master', _('Master spécialisé')),
        ('Autre', _('Autre'))
    ]

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom de famille"),
        }),
        validators=[MaxLengthValidator(50)],
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Prénom"),
        }),
        validators=[MaxLengthValidator(50)],
    )

    formation = forms.ChoiceField(
        choices=FORMATIONS,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse e-mail"),
        }),
        validators=[EmailValidator()]
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Choisissez un mot de passe sécurisé"),
        }),
        validators=[MinLengthValidator(7)],
    )

    password_verification = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre mot de passe")
        }),
        validators=[],
    )

    campus = forms.ChoiceField(
        choices=CAMPUS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': _("Campus"),
        })
    )

    building = forms.ChoiceField(
        choices=BUILDINGS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': _("Bâtiment"),
        }),
    )

    room = forms.IntegerField(
        min_value=0,
        max_value=330,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("N° de Chambre"),
        }),
        required=False,
    )

    address = forms.CharField(
        max_length=512,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse postale complète"),
            'rows': '5'
        }),
        required=False,
    )

    phone = PhoneNumberField(
        widget=PhoneNumberField.widget(attrs={
            'class': 'form-control',
            'placeholder': _("Numéro de téléphone"),
        })
    )

    certify_truth = forms.BooleanField(
        label=_("Je certifie sur l'honneur que les informations saisies sont correctes."),
        widget=forms.CheckboxInput()
    )

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.match(r'\w+.*', last_name):
            raise ValidationError(message=_("Nom de famille incorrect"), code="WRONG LASTNAME")
        return last_name

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.match(r'\w+.*', first_name) or first_name.startswith("_"):
            raise ValidationError(message=_("Prénom incorrect"), code="WRONG FIRSTNAME")
        return first_name

    def clean_campus(self):
        campus = self.cleaned_data['campus']

        if campus == '0':
            raise ValidationError(message=_("Veuillez sélectionner un campus"), code="NO CAMPUS")
        return campus

    def clean_formation(self):
        formation = self.cleaned_data['formation']

        if formation == '0':
            raise ValidationError(message=_("Veuillez sélectionner une formation"), code="NO FORMATION")
        return formation

    def clean_email(self):
        email = self.cleaned_data['email']
        # return email # TODO: debug
        if len(LdapUser.filter(mail=email)) > 0:
            raise ValidationError(message=_("L'addresse email est déjà associée à un compte"), code="USED EMAIL")
        return email

    def clean(self):
        cleaned_data = super(InscriptionForm, self).clean()
        campus = cleaned_data.get("campus")
        building = cleaned_data.get("building")
        address = cleaned_data.get("address")
        room = cleaned_data.get("room")

        if (campus == "Brest" or campus == "Rennes") and room is None:
            self.add_error("room", _("Ce champ est obligatoire"))
        if campus == "Brest" and building not in [a[0] for a in self.BUILDINGS_BREST]:
            self.add_error('building', _("Veuillez choisir un bâtiment du campus de Brest"))
        if campus == "Rennes" and building not in [a[0] for a in self.BUILDINGS_RENNES]:
            self.add_error('building', _("Veuillez choisir un bâtiment du campus de Rennes"))
        if campus == "None" and address == "":
            self.add_error('address', _("Veuillez saisir votre addresse postale"))

        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password_verification')

        if password1 is not None and password1 != password2:
            self.add_error('password',
                           ValidationError(message=_("Les mots de passes sont différents."), code="NOT SAME PASSWORD"))

    @staticmethod
    def get_free_uid(first_name, last_name):
        """
        Check the ldap to get a free uid in the form
        first_name.lower()[0] + last_name.lower()[:8] + xx

        where xx is 2 numbers incremented
        :param first_name:
        :param last_name:
        :return:
        """
        last_name = last_name.lower()
        last_name = re.sub('(\W+|_)', '', last_name)
        if len(last_name) == 0:
            raise InvalidUID("The filtered lastname is empty, please use latin char")
        base_uid = slugify(first_name.lower()[0] + last_name.lower()[:8])

        uid_incr = 0
        uid = base_uid

        while uid_incr < 100:
            user_in_db = LdapUser.filter(uid=uid)
            old_user_in_db = LdapOldUser.filter(uid=uid)
            if len(user_in_db + old_user_in_db) == 0:
                break
            uid_incr += 1
            if uid_incr < 10:
                uid = base_uid + "0" + str(uid_incr)
            else:
                uid = base_uid + str(uid_incr)
        else:
            raise InvalidUID("You may have MAY people called %s %s in your database, please take action..."
                             % (first_name, last_name)
                             )

        return uid

    def to_ldap_user(self):
        """
        Convert the data in the form into an ldap user
        :return:
        """
        user = LdapUser()

        user.uid = self.get_free_uid(self.cleaned_data["first_name"], self.cleaned_data["last_name"])
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.display_name = self.cleaned_data["first_name"] + ' ' + self.cleaned_data["last_name"]
        user.user_password = self.cleaned_data["password"]
        user.nt_password = self.cleaned_data["password"]
        user.postal_address = self.cleaned_data["address"]  # TODO: generate from maisel attributes

        user.cotiz = ''  # FIXME: ''BLACKLIST' + str(current_year()) no cotisation needed
        user.campus = self.cleaned_data["campus"]

        user.building = self.cleaned_data["building"]
        user.room_number = str(self.cleaned_data["room"])

        user.promo = str(current_year() + 3)  # TODO: wtf???
        user.mail = self.cleaned_data["email"]
        user.anneeScolaire = ""  # TODO: get that in school ldap
        user.formation = self.cleaned_data["formation"]
        user.mobile = str(self.cleaned_data["phone"])  # TODO: delete phone field, not very convenient for aliens
        user.option = self.cleaned_data["campus"]
        return user


class CGUForm(forms.Form):
    have_read = forms.BooleanField(
        label=_("En cochant cette case je certifie avoir lu et accepté le règlement intérieur de l'association."),
        widget=forms.CheckboxInput()
    )


class ModPasswdForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Choisissez un mot de passe sécurisé"),
        }),
        validators=[MinLengthValidator(7)],
    )

    password_verification = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre mot de passe")
        }),
        validators=[],
    )

    def clean(self):
        cleaned_data = super(ModPasswdForm, self).clean()
        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password_verification')

        if password1 != password2:
            self.add_error("password", ValidationError(message=_("Les mots de passes sont différents."), code="DIFFERENT PASSWORD"))
        return cleaned_data
