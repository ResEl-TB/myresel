from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class AjoutForm(forms.Form):
    alias = forms.CharField(label = _("Alias de la machine"), required = False)
    
class AjoutManuelForm(forms.Form):
    mac = forms.CharField(label = _("Adresse MAC de la machine"))
    description = forms.CharField(label = _("Description de l'équipement à ajouter"), widget = forms.Textarea)