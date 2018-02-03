# coding: utf-8
import logging
import random

import yaml
import json
import requests

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView, DetailView
from django.views.i18n import set_language
from django.utils import timezone
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from fonctions import network, decorators
from fonctions.decorators import resel_required
from devices.models import LdapDevice
from gestion_personnes.models import LdapUser, UserMetaData
from pages.forms import ContactForm
from pages.models import News, Faq
from wiki.models import Category
from campus.models import RoomBooking
from campus.models.clubs_models import StudentOrganisation
from campus.models.mails_models import Mail
from campus.whoswho.views import ListBirthdays

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

        # Load some campus events
        events = RoomBooking.objects.order_by('start_time').filter(start_time__gt=timezone.now(), displayable=True).all()[:4]
        args_for_response['campus_events'] = events

        # Load some clubs
        clubs = [c for c in StudentOrganisation.all() if "tbClub" in c.object_classes]
        if len(clubs) > 3:
            date = timezone.now()
            random.seed(a=date.day + 100 * date.month + 10000*date.year)
            clubs = random.sample(clubs, 3)
        args_for_response['clubs'] = clubs

        # Load some birthdays
        birthdays_users = ListBirthdays.get_today_birthdays()
        args_for_response['birthdays_users'] = birthdays_users

        # Load some campus mails
        args_for_response['campus_mails'] = Mail.objects.order_by('-date').filter(moderated=True).all()[:settings.NUMBER_NEWS_IN_HOME]

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

class NewsRSS(Feed):
    title = _("Les dernières infos ResEl")
    link = "/rss-news/"
    description = _("Des informations sur l'état du réseau sur les campus de Brest et Rennes")

    def items(self):
        return News.objects.order_by('-date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return reverse('piece-of-news', args=[item.pk])


class NewsAtom(NewsRSS):
    feed_type = Atom1Feed
    subtitle = NewsRSS.description


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


@resel_required
def inscription_zone_info(request):
    """
    View which explains the users on how to register to the ResEl

    If the device is not registered show the information
    If the device is simply not active, it redirect the user to the
    reactivation view
    :param request:
    :return: HttpResponse
    """
    is_registered = False
    is_active = False

    campus = network.get_campus(request.network_data['ip'])
    mac = network.get_mac(request.network_data['ip'])
    vlan = request.network_data['vlan']
    is_logged_in = request.user.is_authenticated()

    try:
        device = LdapDevice.get(mac_address=mac)
        is_registered = True
        is_active = device.get_status(current_campus=campus) == 'active'
        if not is_active:
            return HttpResponseRedirect(reverse("gestion-machines:reactivation"))
    except ObjectDoesNotExist:
        logger.info("The device with the mac %s was not found in the LDAP" % mac,
                extra={
                    'campus': campus,
                    'vlan': vlan,
                    'is_logged_in': is_logged_in,
                    'device_mac': mac,
                    'message_code': 'UNKNOWN_MAC'
                }
        )

    return render(
        request,
        'pages/inscription_zone_info.html',
        {'vlan': vlan, 'is_logged_in': is_logged_in, 'is_registered': is_registered, 'is_active': is_active}
    )

class FaqList(ListView):
    """ Vue appelée pour afficher les F.A.Q. au niveau du ResEl """

    template_name = 'pages/faq.html'
    context_object_name = 'questions'

    def get_queryset(self):
        return Faq.objects.order_by('-vote').all()

def faqVote(request):

    faq = get_object_or_404(Faq, pk=request.POST.get('faq_id', None))
    vote = request.POST.get('vote', None)
    if vote == "upvote":
        faq.upvote()
    elif vote == "downvote":
        faq.downvote()
    return HttpResponse('OK')


@csrf_exempt
def unsecure_set_language(request):
    """ set_language without a csrf """
    return set_language(request)

# @cache_page(30)
class StatusPageXhr(View):

    @staticmethod
    def set_service_status(icinga_rsp, service, excl):
        max_score = 0
        lvl = service.get('level', 1)  # Default to warning

        if service.get('_hosts', None) is None:
            service['status_text'] = 'Pas de métriques'
            service['status'] = 'default'
            return -1

        for icn_service in icinga_rsp['results']:
            if icn_service['joins']['host']['name'] in service.get('_hosts', []) \
                    and icn_service['attrs']['name'] not in excl:
                max_score = max(max_score, icn_service['attrs']['state'])

        StatusPageXhr.cleanup(service)
        if max_score == 0:
            service['status_text'] = 'Système nominal'
            service['status'] = 'success'
        elif max_score == 1:
            service['status_text'] = 'Incidents mineurs'
            service['status'] = 'warning'
        else:
            service['status_text'] = 'Incidents majeurs'
            service['status'] = 'danger'
        return lvl * max_score

    @staticmethod
    def calc_scores(services, result):
        max_score = 0
        for campus in services['campuses']:
            for section in campus['services']:
                for service in campus['services'][section]:
                    score = StatusPageXhr.set_service_status(
                            result,
                            service,
                            services['exclusions'],
                    )
                    if service.get('essential', False):
                        max_score = max(max_score, score)
                    else:
                        # If a service is non essential, no need to escalate
                        # higher than the level 1
                        max_score = max(max_score, min(score, 1))

        services['global_status_score'] = max_score
        if max_score <= 0:
            services['global_status'] = 'success'
            services['global_status_text'] = 'Tous les services sont nominaux'
        elif max_score <= 1:
            services['global_status'] = 'success'
            services['global_status_text'] = (
                "Incidents mineurs en cours sur le réseau. "
                "L'accès à Internet ne devrait pas être affecté")
        elif max_score <= 3:
            services['global_status'] = 'warning'
            services['global_status_text'] = (
                "Incidents mineurs en cours sur le réseau. "
                "Quelques perturbations de l'accès à internet peuvent se produire")
        else:
            services['global_status'] = 'danger'
            services['global_status_text'] = (
                "Des incidents majeurs sont en cours. "
                "L'accès à Internet est fortement perturbé")

    @staticmethod
    def cleanup(service, mangle=False):
        internals = []
        for k in service:
            if k.startswith('_'):
                internals.append(k)
        for k in internals:
            del service[k]

    @staticmethod
    def get_services():
        services = cache.get('icinga_services')
        if services is not None:
            return services
        with open('myresel/icinga_status.yml', 'r') as doc:
            services = yaml.load(doc)
            cache.set('icinga_services',
                      services,
                      settings.ICINGA_SERVICES_CACHE_DURATION)
            return services

    @staticmethod
    def load_services_status(services):
        result = cache.get(
            'icinga_services_status',
            version=settings.ICINGA_STATUS_CACHE_VERSION)
        if result is not None:
            return result
        try:
            r = requests.post(
                url=settings.ICINGA_BASE_URL + "/v1/objects/services",
                auth=settings.ICINGA_AUTH,
                headers={
                    'Accept': 'application/json',
                    'X-HTTP-Method-Override': 'GET',
                },
                data=json.dumps({
                    "joins": [ "host.name", "host.address" ],
                    "attrs": [
                        "name",
                        "state",
                        "downtime_depth",
                        "acknowledgement"
                    ],
                    "filter": ("service.state != ServiceOK && "
                        "service.downtime_depth == 0.0 && "
                        "service.acknowledgement == 0.0")
                })
            )
            if r.status_code != 200:
                raise ValueError('Icinga responded with %i status code' % r.status_code)
            result = r.json()
        except (requests.exceptions.RequestException, ValueError, TypeError) as err:
            # TODO: create a nice fallback template
            logger.error("Could not load icinga, "
                         "loading default configuration instead: %s " % err)
            result = {}
            with open('myresel/icinga_dummy_resp.yml', 'r') as dummy_resp:
                result = yaml.load(dummy_resp)
        StatusPageXhr.calc_scores(services, result)
        cache.set('icinga_services_status',
                  services,
                  settings.ICINGA_STATUS_CACHE_DURATION,
                  version=settings.ICINGA_STATUS_CACHE_VERSION
        )

        return services

    def get(self, request):
        services = self.get_services()
        services_status = self.load_services_status(services)
        return HttpResponse(json.dumps(services_status), content_type='application/json')

