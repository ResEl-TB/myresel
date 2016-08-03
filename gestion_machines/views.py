from django.shortcuts import render
from django.views.generic import View, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

from ldap3 import MODIFY_REPLACE

from .forms import AddDeviceForm, AjoutManuelForm, ModifierForm
from fonctions import ldap, network
from fonctions.decorators import resel_required, unknown_machine
from django.conf import settings


# Create your views here.
class Reactivation(View):
    """ Vue appelée pour ré-activer une machine d'un utilisateur absent trop longtemps du campus """

    template_name = 'gestion_machines/reactivation.html'

    @method_decorator(resel_required)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Reactivation, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Vérification que la machine est bien à l'user
        machine = ldap.search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % network.get_mac(request.META['REMOTE_ADDR']), ['uidproprio', 'host', 'iphostnumber', 'macaddress'])[0]
        if str(request.user) not in machine.uidproprio[0]:
            messages.error(request, _("Cette machine ne semble pas vous appartenir. Veuillez contacter un administrateur afin de la transférer."))
            return HttpResponseRedirect(reverse('pages:news'))

        # Vérification que la machine est bien désactivée
        status = ldap.get_status(request.META['REMOTE_ADDR'])
        if status != 'inactive':
            messages.info(request, _("Votre machine n'a pas besoin d'être ré-activée."))
            return HttpResponseRedirect(reverse('pages:news'))

        ldap.reactivation(request.META['REMOTE_ADDR'])

        mail = EmailMessage(
                subject="[Reactivation Brest] La machine {} [172.22.{} - {}] par {}".format(machine.host[0], machine.iphostnumber[0], machine.macaddress[0], str(request.user)),
                body="Reactivation de la machine {} appartenant à {}\n\nIP : 172.22.{}\nMAC : {}".format(machine.host[0], str(request.user), machine.iphostnumber[0], machine.macaddress[0]),
                from_email="inscription-bot@resel.fr",
                reply_to=["inscription-bot@resel.fr"],
                to=["inscription-bot@resel.fr", "botanik@resel.fr"],
                headers={'Cc': 'botanik@resel.fr'}
            )
        mail.send()
        
        return render(request, self.template_name)


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
            import time

            # Hostname management
            hostname = ldap.get_free_alias(str(request.user))
            alias = form.cleaned_data['alias']

            # In case the user didn't specified any alias, don't make any
            if hostname == alias:
                alias = False

            # Creating ldap form
            dn = 'host=%s,ou=machines,dc=resel,dc=enst-bretagne,dc=fr' % hostname
            object_class = ['reselMachine']
            attributes = {
                'host': hostname,
                'uidproprio': 'uid=%s,' % str(request.user) + settings.LDAP_DN_PEOPLE,
                'iphostnumber': ldap.get_free_ip(200, 223),
                'macaddress': network.get_mac(request.META['REMOTE_ADDR']),
                'zone': ['User', network.get_campus(request.META['REMOTE_ADDR'])],
                'lastdate': time.strftime('%Y%m%d%H%M%S') + 'Z'
            }

            # Only if the default alias is not kept :
            if alias:
                attributes['hostalias'] = alias

            # Ajout de la fiche au LDAP
            ldap.add(dn, object_class, attributes)

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

class ChangementCampus(View):
    """ Vue appelée lorsque qu'une machine provient d'un campus différent """
    
    template_name = 'gestion_machines/changement-campus.html'

    @method_decorator(resel_required)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChangementCampus, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Vérification du statut de la machine dans le LDAP
        if ldap.get_status(request.META['REMOTE_ADDR']) == 'wrong_campus':
            # Mise à jour de la fiche LDAP
            ldap.update_campus(request.META['REMOTE_ADDR'])

            return render(request, self.template_name)

        # La machine est déjà dans le bon campus, on redirige sur la page d'accueil
        messages.info(request, _("Cette machine est déjà enregistrée comme étant dans le bon campus."))
        return HttpResponseRedirect(reverse('pages:news'))

class Liste(ListView):
    """ Vue appelée pour afficher la liste des machines d'un user """

    template_name = 'gestion_machines/liste.html'
    context_object_name = 'machines'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Liste, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        uid = str(self.request.user)
        res = ldap.search(settings.LDAP_DN_MACHINES, '(&(uidproprio=uid=%(uid)s,%(dn_people)s))' % {'uid': uid, 'dn_people': settings.LDAP_DN_PEOPLE}, ['host', 'macaddress', 'zone', 'hostalias'])
        machines = []
        if res:
            for machine in res:
                statut = None
                if 'inactive' in [z.lower() for z in machine.zone]:
                    statut = 'inactive'
                else:
                    statut = 'active'

                try:
                    alias = machine.hostalias
                except:
                    alias = ''
                    
                machines.append({'host': machine.host[0], 'macaddress': machine.macaddress[0], 'statut': statut, 'alias': alias})
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
