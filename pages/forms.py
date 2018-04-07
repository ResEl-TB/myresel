from django import forms
from captcha.fields import CaptchaField
from django.utils.translation import ugettext_lazy as _


class ContactForm(forms.Form):
    nom = forms.CharField(label=_("Votre nom"), widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    chambre = forms.CharField(label=_("Votre chambre"), required=False, widget=forms.TextInput(
        attrs={'placeholder': _("Bâtiment ET chambre"), 'class': 'form-control'}
    ))
    mail = forms.EmailField(label=_("Votre adresse mail"), widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ))
    demande = forms.CharField(label=_("Votre message"), widget=forms.Textarea(
        attrs={'class': 'form-control', 'style': 'resize:none;'}
    ))
    uid = forms.CharField(label="", widget=forms.HiddenInput(), required=False)
    captcha = CaptchaField()
