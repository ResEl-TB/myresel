# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from django.views.generic import View, ListView

from ldapback.backends.ldap.base import SaveError
from fonctions import ldap, network
from fonctions.decorators import resel_required
from devices.models import LdapDevice
from gestion_personnes.models import LdapUser
from .forms import ManualDeviceAddForm

logger = logging.getLogger("default")


@method_decorator(login_required, name='dispatch')
class ManualAddDeviceView(FormView):
    """ Vue appelée pour que l'utilisateur fasse une demande d'ajout de machine (PS4, Xboite, etc.) """

    template_name = 'devices/manual_add_device.html'
    form_class = ManualDeviceAddForm
    success_url = reverse_lazy('gestion-machines:liste')

    def form_valid(self, form):
        form.send_admin_email(self.request.ldap_user)
        messages.success(self.request, _("Votre demande a été envoyée aux administrateurs. L'un d'eux vous contactera d'ici peu de temps."))
        return super(ManualAddDeviceView, self).form_valid(form)


@method_decorator(login_required, name="dispatch")
class ListDevicesView(ListView):
    """
    View called to show user device list
    """

    template_name = 'devices/list_devices.html'
    context_object_name = 'devices'

    def get_queryset(self):
        return LdapDevice.filter(owner="uid=%(uid)s,%(dn_people)s" % {
                'uid': self.request.ldap_user.uid,
                'dn_people': settings.LDAP_DN_PEOPLE
            })


@method_decorator(login_required, name="dispatch")
class EditDeviceView(View):
    """ Vue appelée pour modifier le nom et l'alias de sa machine """

    template_name = 'devices/edit_device.html'
    #form_class = AddDeviceForm
    form_class = None

    @staticmethod
    def get_user_and_machine(username, mac):
        """
        Check if the mac address exists and is known
        :param username: uid of a user
        :param hostname: device hostname
        :return:
        """
        machine = LdapDevice.get(mac_address=mac)
        ldap_user = LdapUser.get(pk=username)
        if ldap_user.pk != machine.owner:
            raise ObjectDoesNotExist()

        return ldap_user, machine

    def get(self, request, *args, **kwargs):
        mac = self.kwargs.get('mac', '')

        try:
            ldap_user, machine = self.get_user_and_machine(request.ldap_user.uid, mac)
        except ObjectDoesNotExist:
            logger.warning("Tentative de modification d'une machine qui n'existe pas"
                           "\n\nuid: {uid}"
                           "\nmac: {mac}".format(
                uid=request.user.username,
                mac=mac),
                           extra={"uid": request.user.username, "mac": mac},
            )
            messages.error(request, _("Cette machine n'existe pas ou ne vous appartient pas."))
            return HttpResponseRedirect(reverse('gestion-machines:liste'))

        #if machine.aliases:
        #    proposed_alias = machine.aliases[0]
        #else:
        #    proposed_alias = ldap.get_free_alias(str(request.user.username))

        form = self.form_class({'alias': 'NOTHING'})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            alias = form.cleaned_data['alias']
            hostname = self.kwargs.get('host', '')
            try:
                ldap_user, machine = self.get_user_and_machine(request.user.username, hostname)
            except ObjectDoesNotExist:
                logger.warning("Tentative de modification d'une machine qui n'existe pas"
                               "\n\nuid: {uid}"
                               "\nhostname: {hostname}"
                               "\nnew alias: {alias}".format(
                    uid=request.user.username,
                    alias=alias,
                    hostname=hostname),
                               extra={"uid": request.user.username, "new_alias": alias, "device_hostname": hostname}
                )
                messages.error(request, _("Cette machine n'existe pas ou ne vous appartient pas."))
                return HttpResponseRedirect(reverse('gestion-machines:liste'))
            if machine.aliases:
                machine.aliases[0] = alias
            else:
                machine.aliases = [alias]

            try:
                machine.save()
                messages.success(request, _("L'alias de la machine a bien été modifié."))
                return HttpResponseRedirect(reverse('gestion-machines:liste'))
            except SaveError as e:
                messages.error(
                    request,
                    _("Une erreur s'est produite lors de l'enregistrement."
                    " Veuillez re-essayer plus tard"))
                logger.error(
                        "ERROR_SAVING_ALIAS: "
                        "Erreur lors du changement de l'alias de la machine."
                        "uid: {uid} "
                        "hostname: {hostname} "
                        "new alias: {alias} "
                        "error: {error}".format(
                            uid=request.user.username,
                            alias=alias,
                            hostname=hostname,
                            error=e,),
                        extra={
                            "message_code": "ERROR_SAVING_ALIAS",
                            "uid": request.user.username,
                            "new_alias": alias,
                            "device_hostname": hostname,
                            "error": e,
                        }
                )

        return render(request, self.template_name, {'form': form})

