from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class ContactForm(forms.Form):
    nom = forms.CharField(label = _("Votre nom"), widget = forms.TextInput(attrs = {'class': 'form-control'}))
    chambre = forms.CharField(label = _("Votre chambre"), widget = forms.TextInput(attrs = {'placeholder': _("Bâtiment ET chambre"), 'class': 'form-control'}))
    mail = forms.EmailField(label = _("Votre adresse mail"), widget = forms.TextInput(attrs = {'class': 'form-control'}))
    demande = forms.CharField(label = _("Votre demande"), widget = forms.Textarea(attrs = {'class': 'form-control', 'style': 'resize:none;'}))