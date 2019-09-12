import re

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.mail import mail_admins
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from fonctions import ldap
from fonctions.ldap import get_free_alias
from devices.models import LdapDevice


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
        try:
            device = LdapDevice.get(mac_address=mac)
            mail_admins(
                "[Transfert {}]Tentative changement compte machine [{}] {}, ".format(settings.CURRENT_CAMPUS,
                                                                                      device.mac_address,
                                                                                      device.hostname),
                "Un utilisateur (quelconque) a tenté de transférer une machine d'un autre utilisateur vers "
                "son compte. Cette personne va très probablement se manifester sur le support afin de transférer "
                "la machine vers son compte."
                "\n\n HOSTNAME: {}"
                "\n MAC: {}"
                "\n IP: {}"
                "\n UID PROPRIO: {}"
                "\n\n /!\\ Le partage de compte est interdit selon le règlement intérieur /!\\"
                "\n\n ----------"
                "\n Message généré par le site ResEl"
                    .format(device.hostname, device.mac_address, device.ip, device.owner)

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
