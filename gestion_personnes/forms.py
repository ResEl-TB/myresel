from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator

from django.utils.translation import ugettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField


class InscriptionForm(forms.Form):
    BUILDINGS = [(0, _("Selectionnez un Bâtiment"))]
    BUILDINGS += [(i, 'I%d' % i) for i in range(1, 13)]
    FORMATIONS = [
        (0, _("Indiquez votre Formation")),
        ('FIG', _("Ingénieur généraliste (FIG)")),
        ('FIP', _("Ingénieur par alternance (FIP)")),
        ('Master', _("Master spécialisé")),
        ('Autre', _("Autre"))
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
            'placeholder': _("Formation"),
        })
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Choisissez un nom d'utilisateur"),
        }),
        validators=[MaxLengthValidator(20)],
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
        validators=[MinLengthValidator(8)],
    )

    password_verification = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _("Retapez votre mot de passe")
        }),
        validators=[],
    )

    building = forms.ChoiceField(
        choices=BUILDINGS,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': _("Bâtiment"),
        })
    )

    room = forms.IntegerField(
        min_value=0,
        max_value=330,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _("N° de Chambre"),
        })
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

    def clean_password_verification(self):
        password1 = self.cleaned_data['password']
        password2 = self.cleaned_data['password_verification']

        if password1 == password2:
            return password2
        raise ValidationError(message=_("Les mots de passes sont différents."), code="NOT SAME PASSWORD")

    def clean_building(self):
        building = self.cleaned_data['building']

        if building == '0':
            raise ValidationError(message=_("Veuillez sélectionner un bâtiment"), code="NO BUILDING")
        return building

    def clean_formation(self):
        formation = self.cleaned_data['formation']

        if formation == '0':
            raise ValidationError(message=_("Veuillez sélectionner une formation"), code="NO FORMATION")
        return formation