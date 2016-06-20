from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class InscriptionForm(forms.Form):
    BATIMENTS = [(i, 'I%d' % i) for i in range(1, 13)]

    pseudo = forms.CharField(label = _("Pseudo"), widget = forms.TextInput(attrs = {'class': 'form-control'}))
    nom = forms.CharField(label = _("Nom"), widget = forms.TextInput(attrs = {'class': 'form-control'}))
    batiment = forms.ChoiceField(label = _("Bâtiment"), choices = BATIMENTS, widget = forms.Select(attrs = {'class': 'form-control'}))
    mail = forms.EmailField(label = _("Adresse mail"), widget = forms.EmailInput(attrs = {'class': 'form-control'}))
    prenom = forms.CharField(label = _("Prénom"), widget = forms.TextInput(attrs = {'class': 'form-control'}))
    chambre = forms.IntegerField(label = _("Chambre"), min_value = 0, max_value = 330, widget = forms.NumberInput(attrs = {'class': 'form-control'}))
    telephone = forms.RegexField(label = _("Numéro de téléphone"), regex = r'^0[6-7]([0-9]{2}){4}$', widget = forms.TextInput(attrs = {'class': 'form-control'}))
    mot_de_passe = forms.CharField(widget = forms.PasswordInput(attrs = {'class': 'form-control'})) 