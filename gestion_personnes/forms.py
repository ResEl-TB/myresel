import time
import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.utils.text import slugify

from django.utils.translation import ugettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from fonctions.generic import current_year, hash_passwd, hash_to_ntpass
from gestion_personnes.models import LdapUser


class InvalidUID(Exception):
    pass


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
        if len(LdapUser.objects.filter(mail=email)) > 0:
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

    def get_free_uid(self, firstname, lastname):
        """
        Check the ldap to get a free uid in the form
        firstname.lower()[0] + lastname.lower()[:8] + xx

        where xx is 2 numbers incremented
        :param firstname:
        :param lastname:
        :return:
        """
        lastname = lastname.lower()
        lastname = re.sub('(\W+|_)', '', lastname)
        if len(lastname) == 0:
            raise InvalidUID("The filtered lastname is empty, please use latin char")
        base_uid = slugify(firstname.lower()[0] + lastname.lower()[:8])

        uid_incr = 0
        uid = base_uid
        # return uid  # TODO: debug
        while uid_incr < 100:
            user_in_db = LdapUser.objects.filter(uid=uid)
            if len(user_in_db) == 0:
                break
            uid_incr += 1
            if uid_incr < 10:
                uid = base_uid + "0" + str(uid_incr)
            else:
                uid = base_uid + str(uid_incr)
        else:
            raise InvalidUID("You may have MAY people called %s %s in your database, please take action..."
                             % (firstname, lastname)
                             )

        return uid

    def to_ldap_user(self):
        """
        Convert the data in the form into an ldap user
        :return:
        """

        user = LdapUser()
        user.uid = self.get_free_uid(self.cleaned_data["first_name"], self.cleaned_data["last_name"])
        user.firstname = self.cleaned_data["first_name"]
        user.lastname = self.cleaned_data["last_name"]
        user.displayname = self.cleaned_data["first_name"] + ' ' + self.cleaned_data["last_name"]
        user.userPassword = hash_passwd(self.cleaned_data["password"])
        user.ntPassword = hash_to_ntpass(self.cleaned_data["password"])

        user.promo = str(current_year() + 3)
        user.mail = self.cleaned_data["email"]
        user.anneeScolaire = self.cleaned_data["email"]
        user.mobile = str(self.cleaned_data["phone"])
        user.option = self.cleaned_data["campus"]

        user.dateInscr = time.strftime('%Y%m%d%H%M%S') + 'Z'
        user.cotiz = 'BLACKLIST' + str(current_year())
        user.endCotiz = time.strftime('%Y%m%d%H%M%S') + 'Z'

        user.campus = self.cleaned_data["campus"]
        user.batiment = 'I' + self.cleaned_data["building"]
        user.roomNumber = str(self.cleaned_data["room"])
        user.address = self.cleaned_data["address"]

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
        validators=[MinLengthValidator(8)],
    )

    password_verification = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre mot de passe")
        }),
        validators=[],
    )

    def clean_password_verification(self):
        password1 = self.cleaned_data['password']
        password2 = self.cleaned_data['password_verification']

        if password1 == password2:
            return password2
        raise ValidationError(message=_("Les mots de passes sont différents."), code="NOT SAME PASSWORD")
