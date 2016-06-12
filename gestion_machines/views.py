from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

from .forms import AjoutForm
from fonctions import ldap, network

# Create your views here.
class Reactivation(TemplateView):
    template_name = 'gestion_machines/reactivation.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Reactivation, self).dispatch(*args, **kwargs)

	def get(self, request, *args, **kwargs):
        ldap.reactivation(request.META['REMOTE_ADDR'])
        return render(request, self.template_name)

class Ajout(TemplateView):
	template_name = 'gestion_machines/ajout.html'
    form_class = AjoutForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Ajout, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Vérification que la machine n'est pas déjà présente dans le LDAP
        if ldap.get_status(request.META['REMOTE_ADDR']) == False:
            form = self.form_class()
            return render(request, self.template_name, {'form': form})

        # La machine est déjà inscrite, on redirige sur la page d'accueil
        messages.error(request, _("Cette machine est déjà enregistrée sur notre réseau."))
        return HttpResponseRedirect(reverse('home'))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            import time

            # Gestion du nom de l'host
            if form.cleaned_data['alias'] != '':
                host = form.cleaned_data['alias']
                alias = ldap.get_free_alias(request.user)
            else:
                host = ldap.get_free_alias(request.user)
                alias = False

            # Mise en forme du DN et des attributs de la fiche LDAP
            dn = 'host=%s,ou=machines,dc=resel,dc=enst-bretagne,dc=fr' % host
            object_class = ['reselMachine']
            attributes = {
                'host': host,
                'uidproprio': 'uid=%s,' % request.user + DN_PEOPLE,
                'iphostnumber': ldap.get_free_ip(200,223),
                'macaddress': network.get_mac(request.META['REMOTE_ADDR']),
                'zone': ['User', network.get_campus(request.META['REMOTE_ADDR'])],
                'lastdate': time.strftime('%Y%m%d%H%M%S') + 'Z'
            }

            if alias:
                attributes['hostalias'] = alias

            # Ajout de la fiche au LDAP
            ldap.add(dn, object_class, attributes)

            # Re-boot du DNS, DHCP et FW
            network.update_all()

            messages.success(request, _("Votre machine a bien été ajoutée. Veuillez ré-initialiser votre connexion en débranchant/rebranchant le câble ou en vous déconnectant/reconnectant au Wi-Fi."))
            return HttpResponseRedirect(reverse('home'))

        return render(request, self.template_name, {'form': form})

class ChangementCampus(TemplateView):
	template_name = 'gestion_machines/changement-campus.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChangementCampus, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        ldap.update_campus(request.META['REMOTE_ADDR'])
        return render(request, self.template_name)