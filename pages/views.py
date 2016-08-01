from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView

from pages.forms import ContactForm
from fonctions import network, ldap, decorators
from pages.models import News
from gestion_personnes.models import LdapUser

from datetime import datetime

class Home(View):
    """
    La première vue que l'utilisateur va ouvrir lorsqu'il arrive sur le site. L'objectif de cette page est d'être d'être
    la plus simple pour tous les types d'utilisations.

    Du fait des différentes origines et objectifs des utilisateurs il y a plusieurs vues possible :
        - Nouvel utilisateur sur le campus, on lui propose de s'inscrire
        - Utilisateur connecté sur le campus, on lui propose des options pour son compte
        - la personne exterieure qui veut en savoir plus sur le ResEl
        - L'utilisateur à l'exterieur qui veut avoir des infos sur son compte
    """

    template_name = 'pages/home.html'

    @method_decorator(decorators.correct_vlan)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']

        # On vérifie que la machine n'est pas desactivée.
        # Si oui, on bascule vers la page de réactivation
        computer_status = False
        if network.is_resel_ip(ip):
            computer_status = ldap.get_status(ip)

        if computer_status:
            # La machine existe dans le LDAP
            if computer_status == 'inactive':
                # La machine est inactive
                return HttpResponseRedirect(reverse('gestion-machines:reactivation'))

            elif computer_status == 'wrong_campus':
                # La machine n'est pas dans le bon campus
                return HttpResponseRedirect(reverse('gestion-machines:changement-campus'))

        # Si user loggé, on regarde jusqu'à quand il a payé
        end_fee = False
        if request.user.is_authenticated():
            user = ldap.search(settings.LDAP_DN_PEOPLE, '(&(uid=%s))' % str(request.user.username), ['endInternet'])[0]
            if user:
                end_fee = datetime.strptime(str(user.endinternet), '%Y%m%d%H%M%SZ') if 'endinternet' in user.entry_to_json().lower() else False

        return render(request, self.template_name, {'end_fee': end_fee})


class NewsListe(ListView):
    """ Vue appelée pour afficher les news au niveau du ResEl """

    template_name = 'pages/news.html'
    context_object_name = 'derniers_billets'

    def get_queryset(self):
        return News.objects.all()


class Contact(View):
    """ Vue appelée pour contacter les admin en cas de soucis """

    template_name = 'pages/contact.html'
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        try:
            user = LdapUser.objects.get(uid=request.user.username)
            form = self.form_class(
                nom=user.displayName,
                chambre=[user.batiment, user.roomNumber].join(' '),
                mail=user.mail
            )
        except:
            form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Envoi d'un mail à support
            mail = EmailMessage(
                subject = "Message de la part d'un utilisateur",
                body = "%(nom)s souhaite vous contacter\n\nChambre : %(chambre)s\nDemande :\n%(demande)s" % {'nom': form.cleaned_data['nom'], 'chambre': form.cleaned_data['chambre'], 'demande': form.cleaned_data['demande']},
                from_email = "myresel@resel.fr",
                reply_to = [form.cleaned_data['mail']],
                to = ["support@resel.fr"],
            )
            mail.send()

            messages.success(_("Votre demande a bien été envoyée aux administrateurs. L'un d'eux vous répondra d'ici peu."))
            return HttpResponseRedirect(reverse('pages:news'))
        return render(request, self.template_name, {'form': form})

def InscriptionZoneInfo(request):
    # First get device datas
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
        vlan = request.META['VLAN']
        host = request.META['HTTP_HOST']
        zone = network.get_network_zone(ip)
        mac = False
        is_registered = 'Unknown'
        is_logged_in = request.user.is_authenticated()
        if "user" in zone or "inscription" in zone : # As the device is in an inscription or user zone, we can get its mac address
            mac = network.get_mac(ip)
            is_registered = ldap.get_status(ip) == 'active'

    if "inscription" not in zone:
        return HttpResponseRedirect(reverse('pages:news'))

    return render(request, 'pages/inscription_zone_info.html', {'vlan': vlan, 'is_logged_in': is_logged_in, 'is_registered': is_registered})
