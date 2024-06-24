# -*- coding: utf-8 -*-
import re

from django import forms
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.urls import reverse
from django.core.validators import MaxLengthValidator, MinLengthValidator, EmailValidator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField

from fonctions.generic import current_year
from gestion_personnes.models import LdapUser, LdapOldUser, UserMetaData, LdapRoom


# TODO : merge personal info form and Inscription form


class ToggleSelect(forms.RadioSelect):
    template_name = 'gestion_personnes/toggle.html'


class InvalidUID(Exception):
    pass


class ResElEmailValidator:

    # From a csv file we get forbidden domains
    def __init__(self):
        self.restricted_domains = set()
        with open('myresel/forbidden_domains.csv', encoding='utf-8') as file:
            for line in file:
                domain = line.strip()
                if domain:
                    self.restricted_domains.add(domain)

    def __call__(self, value):
        domain = value.split('@')[-1]
        if domain in self.restricted_domains:
            raise ValidationError(
                _("Les adresses e-mail du domaine %(domain)s ne sont pas autorisées"),
                params={'domain': domain},
            )


class PersonalInfoForm(forms.Form):
    CAMPUS = [('Brest', "Brest"), ('Rennes', 'Rennes'), ('Nantes', 'Nantes'),
              ('None', _('Je n\'habite pas à la Maisel'))]
    BUILDINGS_BREST = [('I%d' % i, 'I%d' % i) for i in range(1, 13)]
    BUILDINGS_RENNES = [('S1', 'Studios'), ('C1', 'Chambres')]
    BUILDINGS_NANTES = [(letter, letter)
                        for letter in ['N', 'P', 'Q', 'R', 'S', 'T']]
    BUILDINGS_NANTES += [('PC', 'Pitre Chevalier')]

    BUILDINGS = BUILDINGS_BREST + BUILDINGS_RENNES + BUILDINGS_NANTES

    FORMATIONS = [
        ('FIG', _('Généraliste (FISE/FIG)')),
        ('FIP', _('Par alternance (FISA/FIP/FIL/FIT)')),
        ('Autre', _('Autre'))
    ]

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse e-mail"),
        }),
        validators=[EmailValidator(), ResElEmailValidator()]
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
        max_value=799,
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
        }),
        required=False
    )

    certify_truth = forms.BooleanField(
        label=_(
            "Je certifie sur l'honneur que les informations saisies sont correctes."),
        widget=forms.CheckboxInput()
    )

    def clean_campus(self):
        campus = self.cleaned_data['campus']

        if campus == '0':
            raise ValidationError(
                message=_("Veuillez sélectionner un campus"), code="NO CAMPUS")
        return campus

    def clean_formation(self):
        formation = self.cleaned_data['formation']

        if formation == '0':
            raise ValidationError(
                message=_("Veuillez sélectionner une formation"), code="NO FORMATION")
        return formation

    def clean(self):
        cleaned_data = super(PersonalInfoForm, self).clean()
        campus = cleaned_data.get("campus")
        building = cleaned_data.get("building")
        address = cleaned_data.get("address")
        room = cleaned_data.get("room")

        if campus in ['Brest', 'Rennes', 'Nantes'] and room is None:
            self.add_error("room", _("Ce champ est obligatoire"))
        if campus == "Brest" and building not in [a[0] for a in self.BUILDINGS_BREST]:
            self.add_error('building', _(
                "Veuillez choisir un bâtiment du campus de Brest"))
        if campus == "Rennes" and building not in [a[0] for a in self.BUILDINGS_RENNES]:
            self.add_error('building', _(
                "Veuillez choisir un bâtiment du campus de Rennes"))
        if campus == "None" and address == "":
            self.add_error('address', _(
                "Veuillez saisir votre addresse postale"))

        if LdapRoom.does_room_exist(room, building) is False:
            self.add_error('room', _("Ce numéro de chambre est inconnu. \
                          Contactez-nous si vous pensez que c'est une erreur."))


class InscriptionForm(forms.Form):
    CAMPUS = [('Brest', "Brest"), ('Rennes', 'Rennes'), ('Nantes', 'Nantes'),
              ('None', _('Je n\'habite pas à la Maisel'))]
    BUILDINGS_BREST = [('I%d' % i, 'I%d' % i) for i in range(1, 15)]
    BUILDINGS_RENNES = [('S1', 'Studios'), ('C1', 'Chambres')]
    BUILDINGS_NANTES = [(letter, letter)
                        for letter in ['N', 'P', 'Q', 'R', 'S', 'T']]
    BUILDINGS_NANTES += [('PC', 'Pitre Chevalier')]

    BUILDINGS = BUILDINGS_BREST + BUILDINGS_RENNES + BUILDINGS_NANTES

    CATEGORIES = [('student', _('Étudiant(e)')), ('employee', _('Personnel IMT Atlantique')),
                  ('maisel', _('Employé(e) Maisel/MDE')), ('other', _('Autre'))]

    FORMATIONS = [
        ('FIG', _('Généraliste (FISE/FIG)')),
        ('FIP', _('Par alternance (FISA/FIP/FIL/FIT)')),
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

    category = forms.ChoiceField(
        choices=CATEGORIES,
        widget=ToggleSelect()
    )

    formation = forms.ChoiceField(
        choices=FORMATIONS,
        widget=ToggleSelect(),
        required=False,
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse e-mail"),
        }),
        validators=[EmailValidator(), ResElEmailValidator()]
    )

    email_verification = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre adresse e-mail")
        }),
        validators=[],
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Choisissez un mot de passe sécurisé"),
        }),
        validators=[MinLengthValidator(10), MaxLengthValidator(63)]
        # 63 -> Longueur maximum sur certaines implémentations
    )

    password_verification = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre mot de passe")
        }),
        validators=[],
    )

    birth_place = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Ville de naissance"),
        }),
        validators=[MaxLengthValidator(60)],
    )

    birth_country = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Pays de naissance"),
        }),
        validators=[MaxLengthValidator(50)],
    )

    birth_date = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Date de naissance"),
        }),
        validators=[MaxLengthValidator(10)],
    )

    campus = forms.ChoiceField(
        choices=CAMPUS,
        widget=ToggleSelect()
    )

    building = forms.ChoiceField(
        choices=BUILDINGS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': _("Bâtiment"),
        }),
        required=False,
    )

    room = forms.IntegerField(
        min_value=0,
        max_value=799,
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
        }),
        required=False,
    )

    certify_truth = forms.BooleanField(
        label=_(
            "Je certifie sur l'honneur que les informations saisies sont correctes."),
        widget=forms.CheckboxInput()
    )

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.match(r'\w+.*', last_name):
            raise ValidationError(
                message=_("Nom de famille incorrect"), code="WRONG_LASTNAME")
        return last_name

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.match(r'\w+.*', first_name) or first_name.startswith("_"):
            raise ValidationError(
                message=_("Prénom incorrect"), code="WRONG_FIRSTNAME")
        return first_name

    def clean_campus(self):
        campus = self.cleaned_data['campus']
        if campus not in [a[0] for a in self.CAMPUS]:
            raise ValidationError(
                message=_("Veuillez sélectionner un campus"), code="NO_CAMPUS")
        return campus

    def clean_category(self):
        category = self.cleaned_data['category']
        if category == "other":
            raise ValidationError(
                message=_("Vous n’êtes pas éligible à un compte ResEl"), code="NOT_ELIGIBLE")
        if category not in [a[0] for a in self.CATEGORIES]:
            raise ValidationError(
                message=_("Veuillez sélectionner une catégorie valide"), code="NO_CATEGORY")
        return category

    def clean_email(self):
        email = self.cleaned_data['email']
        # return email # TODO: debug
        if len(LdapUser.filter(mail=email)) > 0:
            raise ValidationError(
                message=_("L'addresse email est déjà associée à un compte"), code="USED_EMAIL")
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if not re.match(r'(\d{2}|XX)/(\d{2}|XX)/(\d{4}|XXXX)', birth_date):
            raise ValidationError(
                message=_("Date de naissance incorrecte"), code="WRONG_BIRTHDATE")
        return birth_date

    def clean(self):
        cleaned_data = super(InscriptionForm, self).clean()
        campus = cleaned_data.get("campus")
        building = cleaned_data.get("building")
        address = cleaned_data.get("address")
        room = cleaned_data.get("room")
        formation = cleaned_data.get("formation")
        category = cleaned_data.get("category")

        if (campus in ["Brest", "Rennes", "Nantes"]):
            if not room:
                self.add_error("room", _("Ce champ est obligatoire"))
            if campus == "Brest" and building not in [a[0] for a in self.BUILDINGS_BREST]:
                self.add_error('building', _(
                    "Veuillez choisir un bâtiment du campus de Brest"))
            if campus == "Rennes" and building not in [a[0] for a in self.BUILDINGS_RENNES]:
                self.add_error('building', _(
                    "Veuillez choisir un bâtiment du campus de Rennes"))
            if campus == "Nantes" and building not in [a[0] for a in self.BUILDINGS_NANTES]:
                self.add_error('building', _(
                    "Veuillez choisir un bâtiment du campus de Rennes"))
        elif not address:
            self.add_error('address', _(
                "Veuillez saisir votre addresse postale"))

        if LdapRoom.does_room_exist(room, building) is False:
            self.add_error('room', _("Ce numéro de chambre est inconnu. \
                          Contactez-nous si vous pensez que c'est une erreur."))

        if category == "student" and formation not in [a[0] for a in self.FORMATIONS]:
            self.add_error('formation', _("Veuillez choisir une formation"))

        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password_verification')

        email1 = cleaned_data.get("email")
        email2 = cleaned_data.get("email_verification")

        if email1 is not None and email1 != email2:
            self.add_error("email",
                           ValidationError(message=_("Les adresses e-mail sont différentes."), code="DIFFERENT EMAIL"))

        if password1 is not None and password1 != password2:
            self.add_error('password',
                           ValidationError(message=_("Les mots de passes sont différents."), code="NOT SAME PASSWORD"))

    @ staticmethod
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
            raise InvalidUID(
                "The filtered lastname is empty, please use latin char")
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

        # genericPerson
        # TODO: get that in school ldap
        user.uid = self.get_free_uid(
            self.cleaned_data["first_name"], self.cleaned_data["last_name"])
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.display_name = self.cleaned_data["first_name"] + \
            ' ' + self.cleaned_data["last_name"]
        user.user_password = self.cleaned_data["password"]
        user.nt_password = self.cleaned_data["password"]

        # reselPerson
        user.mail = self.cleaned_data["email"]
        user.mobile = str(self.cleaned_data["phone"])
        # requirement for the admin interface
        user.cotiz = ['NONE' + str(current_year())]
        user.campus = self.cleaned_data["campus"]
        user.birth_place = self.cleaned_data["birth_place"]
        user.birth_country = self.cleaned_data["birth_country"]
        user.freeform_birth_date = self.cleaned_data["birth_date"]

        address = self.cleaned_data["address"]
        if address:
            user.postal_address = address
        else:
            # maiselPerson
            user.building = self.cleaned_data["building"]
            user.room_number = str(self.cleaned_data["room"])
            user.postal_address = user.generate_address(
                user.campus, user.building, user.room_number)

        category = self.cleaned_data["category"]
        if category == "student":
            # enstPerson
            user.promo = str(current_year() + 3)  # TODO: wtf???
            user.anneeScolaire = ""  # TODO: get that in school ldap
            user.option = self.cleaned_data["campus"]
            user.formation = self.cleaned_data["formation"]
        elif category == "maisel":
            user.employee_type = "staff"

        return user


class CGUForm(forms.Form):
    have_read = forms.BooleanField(
        label=_(
            "En cochant cette case je certifie avoir lu et accepté le règlement intérieur de l'association."),
        widget=forms.CheckboxInput()
    )


class ResetPwdSendForm(forms.Form):
    uid = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Identifiant ResEl"),
        }),
    )

    def clean_uid(self):
        uid = self.cleaned_data['uid']

        try:
            LdapUser.get(uid=uid)
        except ObjectDoesNotExist:
            raise ValidationError(
                message=_("L'identifiant n'existe pas"), code="WRONG UID")
        return uid

    def send_reset_email(self, request):
        uid = self.cleaned_data['uid']
        user = LdapUser.get(uid=uid)

        user_meta, __ = UserMetaData.objects.get_or_create(uid=uid)
        user_meta.do_reset_pwd_code()

        user_email = EmailMessage(
            subject=_("Réinitialisation du mot de passe ResEl"),
            body=_("Bonjour,\n\n" +
                   "Vous avez demandé la réinitisalisation de votre mot de passe ResEl. Pour la confirmer veuillez cliquer sur le lien suivant : \n" +
                   "%s\n\n" +
                   "------------------------\n\n" +
                   "Si vous pensez que vous recevez cet e-mail par erreur, veuillez l'ignorer. Dans tous les cas, n'hésitez pas à nous contacter " +
                   "à support@resel.fr pour toute question.") % request.build_absolute_uri(
                reverse('gestion-personnes:reset-pwd',
                        kwargs={'key': user_meta.reset_pwd_code, })
            ),
            from_email="secretaire@resel.fr",
            reply_to=["support@resel.fr"],
            to=[user.mail],
        )

        user_email.send()


class ResetPwdForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Choisissez un mot de passe sécurisé"),
        }),
        validators=[MinLengthValidator(7), MaxLengthValidator(50)]
    )

    password_verification = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre mot de passe")
        }),
        validators=[],
    )

    def clean(self):
        cleaned_data = super(ResetPwdForm, self).clean()

        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password_verification')
        if password1 != password2:
            self.add_error("password",
                           ValidationError(message=_("Les mots de passes sont différents."), code="DIFFERENT PASSWORD"))
        return cleaned_data

    def reset_pwd(self, uid):
        pwd = self.cleaned_data["password"]

        user = LdapUser.get(pk=uid)
        user.user_password = pwd
        user.nt_password = pwd
        user.save()

    def send_reset_email(self, uid):
        user = LdapUser.get(uid=uid)

        user_meta, __ = UserMetaData.objects.get_or_create(uid=uid)
        user_meta.do_reset_pwd_code()

        user_email = EmailMessage(
            subject=_("Mot de passe ResEl réinitialisé"),
            body=_("Bonjour,\n\n" +
                   "Vous avez demandé la réinitisalisation de votre mot de passe ResEl.\n" +
                   "Nous vous confirmons bien la réinitisalisation.\n\n" +
                   "------------------------\n\n" +
                   "Si vous pensez que vous recevez cet e-mail par erreur, veuillez l'ignorer. Dans tous les cas, n'hésitez pas à nous contacter " +
                   "à support@resel.fr"),
            from_email="secretaire@resel.fr",
            reply_to=["support@resel.fr"],
            to=[user.mail],
        )

        user_email.send()


class ModPasswdForm(ResetPwdForm):
    pass  # TODO: ask for old passwd


class SendUidForm(forms.Form):
    email = forms.EmailField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Addresse e-mail"),
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email']

        try:
            LdapUser.get(mail=email)
        except ObjectDoesNotExist:
            raise ValidationError(
                message=_("Cette addresse e-mail n'est pas enregistrée"), code="WRONG EMAIL")
        return email

    def send_email(self, request):
        email = self.cleaned_data['email']
        user = LdapUser.get(mail=email)

        user_email = EmailMessage(
            subject=_("Identifiants ResEl"),
            body=_("Bonjour,\n\n" +
                   "Vous venez de demander l'envoi de vos identifiants ResEl, les voici : \n" +
                   "Nom d'utilisateur : %(uid)s\n" +
                   "Mot de passe : ****** (celui que vous avez choisi à l'inscription)\n\n" +
                   "Vous pourrez vous connecter à votre tableau de bord en cliquant sur le lien suiviant : %(url)s\n\n" +
                   "------------------------\n\n" +
                   "Si vous pensez que vous recevez cet e-mail par erreur, veuillez l'ignorer. Dans tous les cas, n'hésitez pas à nous contacter " +
                   "à support@resel.fr pour toute question.") % {'uid': user.uid, 'url': request.build_absolute_uri(reverse('login'))},
            from_email="secretaire@resel.fr",
            reply_to=["support@resel.fr"],
            to=[user.mail],
        )

        user_email.send()


class RoutingMailForm(forms.Form):
    new_routing_address = forms.EmailField(label='', required=False)
