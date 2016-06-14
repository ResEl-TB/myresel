from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class AjoutForm(forms.Form):
    alias = forms.CharField(label = _("Alias de la machine"), required = False, widget = forms.TextInput(attrs = {'class': 'form-control'}))
    
class AjoutManuelForm(forms.Form):
    mac = forms.CharField(label = _("Adresse MAC de la machine"), widget = forms.TextInput(attrs = {'class': 'form-control', 'placeholder': 'xx:xx:xx:xx:xx:xx'}))
    description = forms.CharField(label = _("Description de l'équipement à ajouter"), widget = forms.Textarea(attrs = {'class': 'form-control', 'style': 'resize:none;'}))