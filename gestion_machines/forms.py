from django import forms

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class AjoutForm(forms.Form):
    alias = forms.CharField(label = _("Alias de la machine"), required = False)
    