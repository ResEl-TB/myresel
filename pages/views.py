# coding: utf-8
import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import OperationalError
from django.db import ProgrammingError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView, DetailView

from fonctions import network, decorators
from fonctions.generic import sizeof_fmt
from gestion_machines.models import LdapDevice, PeopleData
from gestion_personnes.models import LdapUser, UserMetaData
from pages.forms import ContactForm
from pages.models import News, Faq
from wiki.models import Category

logger = logging.getLogger("default")


class Home(View):
    """
    La première vue que l'utilisateur va ouvrir lorsqu'il arrive sur le site. L'objectif de cette page est d'être d'être
    la plus simple pour tous les types d'utilisations.

    Du fait des différentes origines et objectifs des utilisateurs il y a plusieurs vues possible :
        - Nouvel utilisateur sur le campus, on lui propose de s'inscrire
        - Utilisateur connecté sur le campus, on lui propose des options pour son compte
        - la personne exterieure qui veut en savoir plus sur le ResEl
        - L'utilisateur à l'exterieur qui veut avoir des infos sur son compte

    TODO: separate this functions in multiple ones...
    """

    template_name = 'pages/home.html'
    exterior_template = 'pages/home/home_ext.html'
    interior_template = 'pages/home/home_int.html'
    logged_template = 'pages/home/home_logged.html'

    @method_decorator(decorators.correct_vlan)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)


    def get(self, request, *args, **kwargs):
        ip = request.network_data['ip']

        template_for_response = self.exterior_template
        args_for_response = {}

        # Load services
        try:
            services = Category.objects.get(name='Services')
            services = services.get_articles_and_links('user' in network.get_network_zone(ip))[:2]
        except Category.DoesNotExist:
            services = []
        args_for_response['services'] = services

        # Load some news
        news = News.objects.order_by('-date').all()[:settings.NUMBER_NEWS_IN_HOME]
        args_for_response['news'] = news

        # Automatically active the computer if it is known
        # Change campus automatically
        is_in_resel = network.is_resel_ip(ip)
        args_for_response['ip_in_resel'] = is_in_resel

        if request.user.is_authenticated():
            end_fee = request.ldap_user.end_cotiz if request.ldap_user.end_cotiz else False

            # Check email validation:
            user_meta = UserMetaData.objects.get_or_create(uid=request.ldap_user.uid)
            args_for_response['user_meta'] = user_meta
            # Check his end fees date
            if is_in_resel:
                try:
                    mac = network.get_mac(request.network_data['ip'])
                    device = LdapDevice.get(mac_address=mac)
                    args_for_response['device'] = device
                    args_for_response['not_user_device'] = device.owner != request.ldap_user.pk
                    args_for_response['is_registered'] = True
                except ObjectDoesNotExist:
                    args_for_response['is_registered'] = False
            template_for_response = self.logged_template
            args_for_response['end_fee'] = end_fee

            # TODO:For the moment show his total amount downloaded, not the per device view
            # TODO: ~once the new fw is done, we should improve that
            try:
                data_down = PeopleData.objects.filter(uid=request.ldap_user.uid, way=PeopleData.DOWN)
                data_up = PeopleData.objects.filter(uid=request.ldap_user.uid, way=PeopleData.UP)

                display_down = sizeof_fmt(sum(d.amount for d in data_down))
                display_up = sizeof_fmt(sum(d.amount for d in data_up))
                args_for_response['data_down'] = display_down
                args_for_response['data_up'] = display_up
            except (OperationalError, ProgrammingError):  # For the sake of stability we will be very loose with errors in that space
                args_for_response['data_down'] = "ERR"
                args_for_response['data_up'] = "ERR"

        elif network.is_resel_ip(ip):
            template_for_response = self.interior_template

        return render(request, template_for_response, args_for_response)


class NewsListe(ListView):
    """ Vue appelée pour afficher les news au niveau du ResEl """

    template_name = 'pages/news.html'
    context_object_name = 'derniers_billets'
    paginate_by = 5

    def get_queryset(self):
        return News.objects.order_by('-date').all()

class NewsDetail(DetailView):
    """ Vue appelée pour afficher un billet particulié """

    template_name = 'pages/piece_of_news.html'
    context_object_name = 'pieceOfNews'
    model = News

class Services(ListView):
    """ Vue appelée pour afficher la liste des services du ResEl """
    template_name = 'pages/service.html'
    context_object_name = 'services'

    def get_queryset(self):
        ip = self.request.network_data['ip']
        try:
            services = Category.objects.get(name='Services')
            services = services.get_articles_and_links('user' in network.get_network_zone(ip))
        except Category.DoesNotExist:
            services = []
        return(services)

class Contact(View):
    """ Vue appelée pour contacter les admin en cas de soucis """

    template_name = 'pages/contact.html'
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        try:
            user = LdapUser.get(pk=request.user.username)
            if user.building != "0":
                room = user.building + ' ' + user.room_number
            else:
                room = None
            form_data = {
                'nom': user.first_name + ' ' + user.last_name,
                'chambre': room,
                'mail': user.mail,
                'uid': request.user,
            }
            form = self.form_class(initial=form_data)
        except ObjectDoesNotExist:
            form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Envoi d'un mail à support
            mail = EmailMessage(
                subject="[Contact] %s" % form.cleaned_data['nom'],
                body="%(nom)s souhaite contacter un administrateur"
                "\n\nChambre : %(chambre)s"
                "\nuid : %(uid)s"
                "\nMessage :"
                "\n\n%(demande)s" % {
                    'uid': form.cleaned_data['uid'],
                    'nom': form.cleaned_data['nom'],
                    'chambre': form.cleaned_data['chambre'],
                    'demande': form.cleaned_data['demande']
                },
                from_email="contact@resel.fr",
                reply_to=[form.cleaned_data['mail']],
                to=["support@resel.fr"],
            )
            mail.send()

            messages.success(request, _("Votre demande a bien été envoyée aux administrateurs. L'un d'eux vous répondra d'ici peu."))
            return HttpResponseRedirect(reverse('home'))
        return render(request, self.template_name, {'form': form})


def inscriptionZoneInfo(request):
    # First get device datas
    vlan = request.network_data['vlan']
    zone = request.network_data['zone']
    mac = network.get_mac(request.network_data['ip'])
    is_registered = False
    is_logged_in = request.user.is_authenticated()
    if "user" in zone or "inscription" in zone:
        try:
            device = LdapDevice.get(mac_address=mac)
            is_registered = device.get_status() == 'active'
            if not is_registered:
                return HttpResponseRedirect(reverse("gestion-machines:reactivation"))
        except ObjectDoesNotExist:
            pass

    if "inscription" not in zone:
        return HttpResponseRedirect(reverse("home"))

    return render(
        request,
        'pages/inscription_zone_info.html',
        {'vlan': vlan, 'is_logged_in': is_logged_in, 'is_registered': is_registered}
    )

class FaqList(ListView):
    """ Vue appelée pour afficher les F.A.Q. au niveau du ResEl """

    template_name = 'pages/faq.html'
    context_object_name = 'questions'

    def get_queryset(self):
        return Faq.objects.order_by('-vote').all()

def faqUpvote(request):

    faq = get_object_or_404(Faq, pk=request.POST['faq_id'])
    faq.upvote()
    return HttpResponse('OK')
