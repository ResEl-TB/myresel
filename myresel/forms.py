from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class ContactForm(forms.Form):
    nom = forms.CharField(label = _("Votre nom"))
    chambre = forms.CharField(label = _("Votre chambre"), widget = forms.TextInput(attrs = {'placeholder': _("Bâtiment ET chambre")}))
    mail = forms.EmailField(label = _("Votre adresse mail"))
    demande = forms.CharField(label = _("Votre demande"), widget = forms.Textarea)