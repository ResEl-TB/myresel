import re

from django import forms
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from fonctions import ldap
from fonctions.ldap import get_free_alias


class AddDeviceForm(forms.Form):
    alias = forms.CharField(
        label=_("Alias de la machine"),
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        ))

    def clean_alias(self):
        alias = self.cleaned_data['alias']

        if len(alias) != 0:
            if len(alias) < 5:
                raise forms.ValidationError(_("Alias trop court (au moins 5 caractères)"), code='TOO SHORT')
            if len(alias) > 20:
                raise forms.ValidationError(_("Alias trop long (au plus 20 caractères)"), code='TOO LONG')

            # I first do that because it might be a common mistake, and no need to display this error to the user
            alias = alias.lower()
            alias = alias.replace("_", "-")

            # slugify the alias to have a good one
            alias_slug = slugify(alias)
            if len(alias_slug) < 5:
                raise forms.ValidationError(
                    _("Alias non conforme, seul les lettres, chiffres et - sont acceptés."),
                    code='INVALID NAME'
                )

            if alias_slug != alias:
                alias_free = get_free_alias(alias_slug, '')
                self.data = self.data.copy()  # Weak hack to modify data
                self.data['alias'] = alias_free
                raise forms.ValidationError(
                    _("Alias non conforme, nous vous proposons un valide à la place."),
                    code='INVALID NAME'
                )

            if ldap.search(settings.LDAP_DN_MACHINES, '(|(host=%(alias)s)(hostalias=%(alias)s))' % {'alias': alias}):
                raise forms.ValidationError(_("Alias déjà utilisé"), code='invalid')

        return alias


class AjoutManuelForm(forms.Form):
    mac = forms.CharField(label=_("Adresse MAC de la machine"),
                          widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'xx:xx:xx:xx:xx:xx'}))
    description = forms.CharField(label=_("Description de l'équipement à ajouter"),
                                  widget=forms.Textarea(attrs={'class': 'form-control', 'style': 'resize:none;'}))

    def clean_mac(self):
        mac = self.cleaned_data['mac']
        if not re.match(r'^([a-f0-9]{2}[:\-]){5}[a-f0-9]{2}$', mac):
            raise forms.ValidationError(_("Adresse MAC non valide"), code='invalid')
        if ldap.search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % mac):
            raise forms.ValidationError(_("Cette machine est déjà enregistrée sur notre réseau."), code='invalid')
        return mac


class ModifierForm(forms.Form):
    alias = forms.CharField(label = _("Alias de la machine"), widget = forms.TextInput(attrs = {'class': 'form-control'}), required=False)

    def clean_alias(self):
        alias = self.cleaned_data['alias']

        if len(alias) == 0:
            return alias

        if len(alias) < 5:
            raise forms.ValidationError(_("Longueur d'alias trop courte"), code='invalid')

        if not re.match(r'^[a-z0-9-]{5,}$', alias):
            raise forms.ValidationError(_("Alias non conforme"), code='invalid')

        if ldap.search(settings.LDAP_DN_MACHINES, '(|(host=%(alias)s)(hostalias=%(alias)s))' % {'alias': alias}):
            raise forms.ValidationError(_("Alias non disponible"), code='invalid')

        return alias
