from django import forms
from myresel.constantes import DN_MACHINES
from fonctions import ldap

import re

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

class AjoutForm(forms.Form):
    alias = forms.CharField(label = _("Alias de la machine"), required = False, widget = forms.TextInput(attrs = {'class': 'form-control'}))

    def clean_alias(self):
        alias = self.cleaned_data['alias']

        if len(alias) != 0:
            if len(alias) < 5:
                raise forms.ValidationError(_("Longueur d'alias trop courte"), code = 'invalid')

            if not re.match(r'^[a-z0-9-]{5,}$', alias):
                raise forms.ValidationError(_("Alias non conforme"), code = 'invalid')

            if not ldap.search(DN_MACHINES, '(|(host=%(alias)s)(hostalias=%(alias)s))' % {'alias': alias}):
                raise forms.ValidationError(_("Alias non disponible"), code = 'invalid')

        return alias
    
class AjoutManuelForm(forms.Form):
    mac = forms.CharField(label = _("Adresse MAC de la machine"), widget = forms.TextInput(attrs = {'class': 'form-control', 'placeholder': 'xx:xx:xx:xx:xx:xx'}))
    description = forms.CharField(label = _("Description de l'équipement à ajouter"), widget = forms.Textarea(attrs = {'class': 'form-control', 'style': 'resize:none;'}))

class ModifierForm(forms.Form):
    machine = None
    uid = None

    def __init__(self, mac, uid):
        super().__init__()
        self.machine = ldap.search(DN_MACHINES, '(&(macaddress=%s))' % mac, ['host', 'hostalias'])[0]
        self.uid = uid

    def get_hostname(self):
        return self.machine.host[0]

    def get_alias(self):
        alias = ''
        for a in self.machine.hostalias:
            if 'pc' + uid not in alias:
                alias = a
        return alias

    host = forms.CharField(label = _("Nom de la machine"), initial = get_hostname, widget = forms.TextInput(attrs = {'class': 'form-control'}))
    alias = forms.CharField(label = _("Alias de la machine"), intial = get_alias, required = False, widget = forms.TextInput(attrs = {'class': 'form-control'}))