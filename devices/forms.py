import re
import unicodedata

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.mail import mail_admins
from django.utils.translation import gettext_lazy as _

from fonctions import ldap
from devices.models import LdapDevice


class EditDeviceForm(forms.Form):
    alias = forms.CharField(label=_("Nom de la machine"), required=False)

    def __init__(self, dic):
        default = dic.pop('default')
        super().__init__(dic)
        if default:
            par = ' (%s)' % default
        else:
            par = ''
        widget = forms.TextInput(attrs={'class': 'form-control',
                                        'placeholder': _("Nom automatique") + par})
        self.fields['alias'].widget = widget

    def clean_alias(self):
        alias = self.cleaned_data['alias']

        if len(alias) == 0:
            return alias

        if len(alias) < 3:
            raise forms.ValidationError(_("Nom trop court (au moins 3 caractères)"), code='TOO SHORT')
        if len(alias) > 20:
            raise forms.ValidationError(_("Nom trop long (au plus 20 caractères)"), code='TOO LONG')

        # Custom slugification
        alias_sl = unicodedata.normalize('NFKD', alias).encode('ascii', 'ignore').decode('ascii')
        alias_sl = re.sub(r'[^\w\s_\-]', '', alias_sl).strip()
        alias_sl = re.sub(r'[_\-\s]+', '-', alias_sl)

        if len(alias_sl) < 3:
            raise forms.ValidationError(
                _("Nom non conforme, seuls les lettres, chiffres et tirets sont acceptés."),
                code='INVALID NAME'
            )

        if alias_sl != alias:
            self.data = self.data.copy()  # Weak hack to modify data
            self.data['alias'] = alias_sl
            raise forms.ValidationError(
                _("Nom non conforme, nous vous proposons celui-ci à la place."),
                code='INVALID NAME'
            )

        return alias_sl


class ManualDeviceAddForm(forms.Form):
    mac = forms.CharField(label=_("Adresse MAC de la machine"),
                          widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'xx:xx:xx:xx:xx:xx'}))
    description = forms.CharField(label=_("Raison de la demande"),
                                  widget=forms.Textarea(attrs={'class': 'form-control', 'style': 'resize:none;'}))

    def clean_mac(self):
        mac = self.cleaned_data['mac']
        mac = mac.lower()
        if not re.match(r'^([a-f0-9]{2}[:\-]){5}[a-f0-9]{2}$', mac):
            raise forms.ValidationError(_("Adresse MAC non valide"), code='invalid')
        mac_addr = mac.replace(':', '').replace('-', '')
        try:
            device = LdapDevice.get(pk=mac_addr)
            mail_admins(
                "[Transfert] Tentative de changement de compte",
                "Un utilisateur (quelconque) a tenté de transférer une machine d'un autre utilisateur vers "
                "son compte. Cette personne va très probablement se manifester sur le support afin de transférer "
                "la machine vers son compte."
                "\n\n MAC: {}"
                "\n UID PROPRIO: {}"
                "\n\n /!\\ Le partage de compte est interdit selon le règlement intérieur /!\\"
                "\n\n ----------"
                "\n Message généré par le site ResEl"
                    .format(device.mac_address, device.owner)

            )
            # Send an email to notify the admins that the device is already saved
            raise forms.ValidationError(_("Cette machine est déjà enregistrée sur notre réseau."), code='invalid')
        except ObjectDoesNotExist:
           pass
        return mac

    def send_admin_email(self, ldap_user):
        """
        Send an email for the support
        :param ldap_user:
        :return:
        """
        mail = EmailMessage(
            subject="Ajout machine sur le compte de %(user)s" % {'user': ldap_user.uid},
            body="L'utilisateur %(user)s souhaite ajouter une machine à son compte."
                 "\n\nuid : %(user)s"
                 "\nPrénom NOM : %(firstname)s %(lastname)s"
                 "\n\nMAC : %(mac)s"
                 "\n\nDescription de la demande:"
                 "\n\n%(desc)s"
                 "\n\n----------------------------"
                 "\nCe message est un message automatique généré par le site resel.fr, il convient de répondre à "
                 "l'utilisateur et non ce message."
                 "\nIl est important de noter que l'utilisateur doit expliquer pourquoi il ne peut pas inscrire sa"
                 "machine normalement, le cas le plus courant étant les consoles de jeu." % {
                     'user': ldap_user.uid,
                     'lastname': ldap_user.last_name.upper(),
                     'firstname': ldap_user.first_name,
                     'mac': self.cleaned_data['mac'],
                     'desc': self.cleaned_data['description']
                 },
            from_email=settings.SERVER_EMAIL,
            reply_to=[ldap_user.mail],
            to=["support@resel.fr"],
        )
        mail.send()
