# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic import View, ListView

from ldapback.backends.ldap.base import SaveError
from fonctions import ldap, network
from fonctions.decorators import resel_required
from devices.models import LdapDevice
from gestion_personnes.models import LdapUser
from .forms import EditDeviceForm, ManualDeviceAddForm

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
    """ Vue appelée pour modifier le nom de sa machine """

    template_name = 'devices/edit_device.html'
    form_class = EditDeviceForm

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
            ldap_user, machine = self.get_user_and_machine(request.user.username, mac)
        except ObjectDoesNotExist:
            logger.warning("Tentative de modification d'une machine qui n'existe pas"
                           "\n\nuid: {uid}"
                           "\nmac: {mac}".format(uid=request.user.username, mac=mac),
                           extra={"uid": request.user.username, "mac": mac})
            messages.error(request, _("Cette machine n'existe pas ou ne vous appartient pas."))
            return HttpResponseRedirect(reverse('gestion-machines:liste'))

        form = self.form_class({'alias': machine.host_alias,
                                'default': machine.host})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        mac = self.kwargs.get('mac', '')

        try:
            ldap_user, machine = self.get_user_and_machine(request.user.username, mac)
        except ObjectDoesNotExist:
            logger.warning("Tentative de modification d'une machine qui n'existe pas"
                           "\n\nuid: {uid}"
                           "\nmac: {mac}".format(uid=request.user.username, mac=mac),
                           extra={"uid": request.user.username, "mac": mac})
            messages.error(request, _("Cette machine n'existe pas ou ne vous appartient pas."))
            return HttpResponseRedirect(reverse('gestion-machines:liste'))

        post_data = request.POST.dict()
        post_data['default'] = machine.host
        form = self.form_class(post_data)

        if form.is_valid():
            alias = form.cleaned_data['alias']
            machine.host_alias = alias

            try:
                machine.save()
                messages.success(request, _("Le nom de la machine a bien été modifié."))
                return HttpResponseRedirect(reverse('gestion-machines:liste'))
            except SaveError as e:
                messages.error(
                    request,
                    _("Une erreur s'est produite lors de l'enregistrement."
                    " Veuillez réessayer plus tard"))
                logger.error(
                        "ERROR_SAVING_HOST: "
                        "Erreur lors du changement du nom de la machine."
                        "uid: {uid} "
                        "mac: {mac} "
                        "new host: {alias} "
                        "error: {error}".format(
                            uid=request.user.username,
                            mac=mac,
                            alias=alias,
                            error=e,),
                        extra={
                            "message_code": "ERROR_SAVING_HOST",
                            "uid": request.user.username,
                            "mac": mac,
                            "new_host": alias,
                            "error": e,
                        }
                )

        return render(request, self.template_name, {'form': form})

