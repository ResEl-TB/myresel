from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

from .forms import *
from fonctions import ldap, network
from fonctions.decorators import resel_required, unknown_machine
from myresel.constantes import DN_MACHINES, DN_PEOPLE

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
        machine = ldap.search(DN_MACHINES, '(&(macaddress=%s))' % network.get_mac(request.META['REMOTE_ADDR']), ['uidproprio'])[0]
        if str(request.user) not in machine.uidproprio[0]:
            messages.error(request, _("Cette machine n'est pas censée vous appartenir. Veuillez contacter un administrateur afin de la transférer."))
            return HttpResponseRedirect(reverse('news'))
            
        # Vérification que la machine est bien désactivée
        status = ldap.get_status(request.META['REMOTE_ADDR'])
        if status != 'inactive':
            messages.info(request, _("Votre machine n'a pas besoin d'être ré-activée."))
            return HttpResponseRedirect(reverse('news'))

        ldap.reactivation(request.META['REMOTE_ADDR'])
        return render(request, self.template_name)

class Ajout(View):
    """ Vue appelée pour l'ajout d'une nouvelle machine """

    template_name = 'gestion_machines/ajout.html'
    form_class = AjoutForm

    @method_decorator(resel_required)
    @method_decorator(unknown_machine)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Ajout, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            import time

            # Gestion du nom de l'host
            if form.cleaned_data['alias'] != '':
                host = form.cleaned_data['alias']
                alias = ldap.get_free_alias(str(request.user))
            else:
                host = ldap.get_free_alias(str(request.user))
                alias = False

            # Mise en forme du DN et des attributs de la fiche LDAP
            dn = 'host=%s,ou=machines,dc=resel,dc=enst-bretagne,dc=fr' % host
            object_class = ['reselMachine']
            attributes = {
                'host': host,
                'uidproprio': 'uid=%s,' % str(request.user) + DN_PEOPLE,
                'iphostnumber': ldap.get_free_ip(200,223),
                'macaddress': network.get_mac(request.META['REMOTE_ADDR']),
                'zone': ['User', network.get_campus(request.META['REMOTE_ADDR'])],
                'lastdate': time.strftime('%Y%m%d%H%M%S') + 'Z'
            }

            if alias:
                attributes['hostalias'] = alias

            # Ajout de la fiche au LDAP
            ldap.add(dn, object_class, attributes)

            messages.success(request, _("Votre machine a bien été ajoutée. Veuillez ré-initialiser votre connexion en débranchant/rebranchant le câble ou en vous déconnectant/reconnectant au Wi-Fi."))
            return HttpResponseRedirect(reverse('news'))

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
            return HttpResponseRedirect(reverse('news'))

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
        if ldap.get_status(request.META['REMOTE_ADDR']) == 'mauvais_campus':
            # Mise à jour de la fiche LDAP
            ldap.update_campus(request.META['REMOTE_ADDR'])

            return render(request, self.template_name)

        # La machine est déjà dans le bon campus, on redirige sur la page d'accueil
        messages.info(request, _("Cette machine est déjà enregistrée comme étant dans le bon campus."))
        return HttpResponseRedirect(reverse('news'))