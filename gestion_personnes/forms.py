from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class InscriptionForm(forms.Form):
    BATIMENTS = [(i, 'I%d' % i) for i in range(1, 13)]

    pseudo = forms.CharField(label = _("Pseudo"))
    nom = forms.CharField(label = _("Nom"))
    prenom = forms.CharField(label = _("Prénom"))
    mail = forms.EmailField(label = _("Adresse mail"))
    batiment = forms.ChoiceField(label = _("Bâtiment"), choices = BATIMENTS)
    chambre = forms.IntegerField(label = _("Chambre"), min_value = 0, max_value = 330)
    telephone = forms.RegexField(label = _("Numéro de téléphone"), regex = r'^0[6-7]([0-9]{2}){4}$')
    mot_de_passe = forms.CharField(widget = forms.PasswordInput) 