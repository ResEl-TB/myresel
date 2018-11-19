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
from fonctions.decorators import resel_required, unknown_machine
from fonctions.network import get_campus
from devices.models import LdapDevice
from gestion_personnes.models import LdapUser
from .forms import AddDeviceForm, ManualDeviceAddForm

logger = logging.getLogger("default")


@method_decorator(resel_required, name="dispatch")
class Reactivation(View):
    """
    Vue appelée pour ré-activer une machine d'un utilisateur absent trop longtemps du campus
    Would a post REQUEST more adequate ? Maybe hard to implement.
    """
    def get(self, request, *args, **kwargs):
        mac = network.get_mac(request.network_data['ip'])
        campus = network.get_campus(request.network_data['ip'])

        try:
            device = LdapDevice.get(mac_address=mac)
        except ObjectDoesNotExist:
            logger.warning("the device with the mac %s was meant to be reactivated, but it is not in the ldap" % mac,
                        extra={
                            'device_mac': mac,
                            'device_ip': request.network_data['ip'],
                            'message_code': 'REACTIVATION_TRY_BUT_UNKNOWN'
                        })
            return HttpResponseRedirect(reverse('home'))

        if device.get_status(current_campus=campus) == 'active':
            logger.warning("the device with the mac %s was meant to be reactivated, but it is already activated" % mac,
                           extra={
                               'device_mac': mac,
                               'device_ip': request.network_data['ip'],
                               'message_code': 'REACTIVATION_BUT_ALREADY'
                           })
            messages.info(request,
                          _("Votre machine n'a pas besoin d'être ré-activée. "
                            "Si le problème persiste veuillez contacter un administrateur."))
            return HttpResponseRedirect(reverse('home'))

        device.activate(campus=campus)
        device.save()
        owner_uid = device.owner.split(',')[0][4:]
        network.update_all()
        logger.info("the device with the mac %s was reactivated" % mac,
            extra={
               'campus': campus,
               'device_mac': mac,
               'device_previous_ip': request.network_data['ip'],
               'device_ip': device.ip,
               'device_hostname': device.hostname,
               'message_code': 'REACTIVATION'
            })
        mail_admins(
            "[Reactivation {}] 172.22.{} - {} [{}] par {}".format(settings.CURRENT_CAMPUS,
                                                                  device.ip, device.mac_address, device.hostname,
                                                                  owner_uid),
            "Reactivation de la machine {} appartenant à {}\n\nIP : 172.22.{}\nMAC : {}".format(device.hostname,
                                                                                                owner_uid,
                                                                                                device.ip,
                                                                                                device.mac_address)
        )
        messages.info(request, _("Votre machine vient d'être réactivée."))

        return HttpResponseRedirect(reverse('home'))


@method_decorator(resel_required, name="dispatch")
@method_decorator(unknown_machine, name="dispatch")
@method_decorator(login_required, name="dispatch")
class AddDeviceView(View):
    """
    View called when a user want to add a new device to his account
    He can choose an alias. If he leave the default alias, he will have no
    alias.
    """

    template_name = 'devices/add_device.html'
    form_class = AddDeviceForm

    def get(self, request, *args, **kwargs):
        proposed_alias = ldap.get_free_alias(str(request.user))

        form = self.form_class({'alias': proposed_alias})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():

            # Hostname management
            hostname = ldap.get_free_alias(str(request.user))
            alias = form.cleaned_data['alias']
            campus = get_campus(request.network_data['ip'])
            mac = network.get_mac(request.network_data['ip'])

            # In case the user didn't specified any alias, don't make any
            if hostname == alias:
                alias = False

            # Creating ldap form
            device = LdapDevice()
            device.hostname = hostname
            device.set_owner(request.user)
            device.ip = ldap.get_free_ip(200, 223)  # TODO: move that to settings
            device.mac_address = mac

            if alias:  # If a user choose an alias, add it
                device.add_alias(alias)

            device.activate(campus)

            # I think even with the decorator, some user where able to click twice on the submit button fast enough
            # To create a bug... So we check one final time before saving the data
            if len(LdapDevice.filter(mac_address=mac)) > 0:
                messages.error(request, _(
                    "Votre machine est déjà enregistrée sur notre réseau. Si vous pensez que c'est une erreur n'hésitez pas à contactez un administrateur."
                ))
                return render(request, self.template_name, {'form': form})
            device.save()
            network.update_all()  # Warning, this command is long see implementation for more details

            mail_admins(
                "[Inscription {}] 172.22.{} - {} [{}] par {}".format(settings.CURRENT_CAMPUS,
                                                                     device.ip, device.mac_address,
                                                                     device.hostname,
                                                                     str(request.user)),
                "Inscription de la machine {} appartenant à {}\n\nIP : 172.22.{}\nMAC : {}".format(device.hostname,
                                                                                                   str(request.user),
                                                                                                   device.ip,
                                                                                                   device.mac_address)

            )

            messages.success(request, _(
                "Votre machine a bien été ajoutée. Veuillez ré-initialiser votre connexion en débranchant/rebranchant le câble ou en vous déconnectant/reconnectant au Wi-Fi ResEl Secure."))
            return HttpResponseRedirect(reverse('home'))

        return render(request, self.template_name, {'form': form})


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
    form_class = AddDeviceForm

    @staticmethod
    def get_user_and_machine(username, hostname):
        """
        Check if the mac address exists and is known
        :param username: uid of a user
        :param hostname: device hostname
        :return:
        """
        machine = LdapDevice.get(hostname=hostname)
        ldap_user = LdapUser.get(pk=username)
        if ldap_user.pk != machine.owner:
            raise ObjectDoesNotExist()

        return ldap_user, machine

    def get(self, request, *args, **kwargs):
        hostname = self.kwargs.get('host', '')

        # Check if the device belongs to the logged in user
        try:
            ldap_user, machine = self.get_user_and_machine(request.ldap_user.uid, hostname)
        except ObjectDoesNotExist:
            logger.warning("Tentative de modification d'une machine qui n'existe pas"
                           "\n\nuid: {uid}"
                           "\nhostname: {hostname}".format(
                uid=request.user.username,
                hostname=hostname),
                           extra={"uid": request.user.username, "device_hostname": hostname},
            )
            messages.error(request, _("Cette machine n'existe pas ou ne vous appartient pas."))
            return HttpResponseRedirect(reverse('gestion-machines:liste'))

        if machine.aliases:
            proposed_alias = machine.aliases[0]
        else:
            proposed_alias = ldap.get_free_alias(str(request.user.username))

        form = self.form_class({'alias': proposed_alias})
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

