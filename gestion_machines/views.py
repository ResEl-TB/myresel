# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView
from ldap3 import MODIFY_REPLACE

from fonctions import ldap, network
from fonctions.decorators import resel_required, unknown_machine
from fonctions.network import get_campus
from gestion_machines.models import LdapDevice
from .forms import AddDeviceForm, AjoutManuelForm, ModifierForm


# Create your views here.
class Reactivation(View):
    """
    Vue appelée pour ré-activer une machine d'un utilisateur absent trop longtemps du campus
    Would a post REQUEST more adequate ? Maybe hard to implement.
    """

    @method_decorator(resel_required)
    def dispatch(self, *args, **kwargs):
        return super(Reactivation, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        mac = request.network_data['mac']

        try:
            device = LdapDevice.get(mac_address=mac)
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('home'))

        if device.get_status() == 'active':
            messages.info(request, _("Votre machine n'a pas besoin d'être ré-activée."))
            return HttpResponseRedirect(reverse('home'))

        device.activate(campus=settings.CURRENT_CAMPUS)
        device.save()

        mail = EmailMessage(
                subject="[Reactivation {}] La machine {} [172.22.{} - {}] par {}".format(settings.CURRENT_CAMPUS, device.hostname, device.ip, device.mac_address, str(request.user)),
                body="Reactivation de la machine {} appartenant à {}\n\nIP : 172.22.{}\nMAC : {}".format(device.hostname, str(request.user), device.ip, device.mac_address),
                from_email="inscription-bot@resel.fr",
                reply_to=["inscription-bot@resel.fr"],
                to=["inscription-bot@resel.fr", "botanik@resel.fr"],
                headers={'Cc': 'botanik@resel.fr'}
            )
        try:
            mail.send()
        except Exception:
            pass
        messages.info(request, _("Votre machine a bien été activée."))
        network.update_all()

        return HttpResponseRedirect(reverse('home'))


class AddDeviceView(View):
    """
    View called when a user want to add a new device to his account
    He can choose an alias. If he leave the default alias, he will have no
    alias.
    """

    template_name = 'gestion_machines/add_device.html'
    form_class = AddDeviceForm

    @method_decorator(resel_required)
    @method_decorator(unknown_machine)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddDeviceView, self).dispatch(*args, **kwargs)

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

            # In case the user didn't specified any alias, don't make any
            if hostname == alias:
                alias = False

            # Creating ldap form
            device = LdapDevice()
            device.hostname = hostname
            device.set_owner(request.user)
            device.ip = ldap.get_free_ip(200, 223)  # TODO: move that to setttings
            device.mac_address = request.network_data['mac']

            if alias:
                device.add_alias(alias)

            device.activate(campus)
            device.save()
            network.update_all()  # TODO: Move that to something async

            messages.success(request, _("Votre machine a bien été ajoutée. Veuillez ré-initialiser votre connexion en débranchant/rebranchant le câble ou en vous déconnectant/reconnectant au Wi-Fi ResEl Secure."))
            return HttpResponseRedirect(reverse('home'))

        return render(request, self.template_name, {'form': form})


class AjoutManuel(View):
    """ Vue appelée pour que l'utilisateur fasse une demande d'ajout de machine (PS4, Xboite, etc.) """

    template_name = 'gestion_machines/ajout-manuel.html'
    form_class = AjoutManuelForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AjoutManuel, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Envoi d'un mail à support
            mail = EmailMessage(
                subject = "Demande d'ajout d'une machine",
                body = "L'utilisateur %(user)s souhaite ajouter une machine à son compte.\n\n MAC : %(mac)s\nDescription de la demande :\n%(desc)s" % {'user': str(request.user), 'mac': form.cleaned_data['mac'], 'desc': form.cleaned_data['description']},
                from_email = "myresel@resel.fr",
                reply_to = ["noreply@resel.fr"],
                to = ["support@resel.fr"],
            )
            mail.send()

            messages.success(request, _("Votre demande a été envoyée aux administrateurs. L'un d'eux vous contactera d'ici peu de temps."))
            return HttpResponseRedirect(reverse('pages:news'))

        return render(request, self.template_name, {'form': form})


class Liste(ListView):
    """
    View called to show user device list
    """

    template_name = 'gestion_machines/list_devices.html'
    context_object_name = 'machines'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Liste, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        uid = str(self.request.user)
        devices = LdapDevice.search(owner="uid=%(uid)s,%(dn_people)s" % {'uid': uid, 'dn_people': settings.LDAP_DN_PEOPLE})

        machines = []
        for device in devices:
            status = device.get_status()
            alias = device.aliases
            machines.append(
                {'host': device.hostname, 'macaddress': device.mac_address, 'statut': status, 'alias': alias})
        return machines


class Modifier(View):
    """ Vue appelée pour modifier le nom et l'alias de sa machine """

    template_name = 'gestion_machines/modifier.html'
    form_class = ModifierForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Modifier, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        host = self.kwargs.get('host', '')

        # Vérification que la mac fournie est connue, et que la machine appartient à l'user
        machine = ldap.search(settings.LDAP_DN_MACHINES, '(&(host=%s))' % host, ['uidproprio', 'hostalias'])
        if machine:
            if str(request.user) not in machine[0].entry_to_json():
                messages.error(request, _("Cette machine ne vous appartient pas."))
                return HttpResponseRedirect(reverse('pages:news'))

            alias = ''
            try:
                for a in machine[0].hostalias:
                    if 'pc' + str(request.user) in a:
                        request.session['generic_alias'] = a
                    else:
                        alias = a

            except:
                alias = ''
                request.session['generic_alias'] = machine[0].host[0]

            if alias != '':
                form = self.form_class({'alias': alias})
            else:
                form = self.form_class()
            
            return render(request, self.template_name, {'form': form})
        else:
            messages.error(request, _("Cette machine n'est pas connue sur notre réseau."))
            return HttpResponseRedirect(reverse('pages:news'))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            dn = 'host=%s,' % self.kwargs.get('host', '') + settings.LDAP_DN_MACHINES
            modifs = {'hostAlias': [(MODIFY_REPLACE, [request.session['generic_alias'], form.cleaned_data['alias']])]}
            print(modifs)
            ldap.modify(dn, modifs)
            network.update_all()

            del(request.session['generic_alias'])
            messages.success(request, _("L'alias de la machine a bien été modifié."))
            return HttpResponseRedirect(reverse('gestion-machines:liste'))

        return render(request, self.template_name, {'form': form})
