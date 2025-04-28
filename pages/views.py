# coding: utf-8
import os
import logging
import datetime

import json
import requests
import yaml

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import EmailMessage
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseServerError
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.views.generic import View, ListView, DetailView, TemplateView
from django.views.i18n import set_language
from django.utils import timezone
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from fonctions.decorators import resel_required
from gestion_personnes.models import LdapUser, UserMetaData
from pages.forms import ContactForm
from pages.models import News, Faq
from wiki.models import Category
from campus.models import RoomBooking
from campus.models.mails_models import Mail

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

    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)


    def get(self, request, *args, **kwargs):
        ip = request.network_data['ip']

        template_for_response = self.exterior_template
        args_for_response = {}

        # Load services
        try:
            services = Category.objects.get(name='Services')
            services = services.get_articles_and_links(request.network_data['subnet'] == 'USER')[:2]
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
        #clubs = [c for c in StudentOrganisation.all() if "tbClub" in c.object_classes]
        #if len(clubs) > 3:
        #    date = timezone.now()
        #    random.seed(a=date.day + 100 * date.month + 10000*date.year)
        #    clubs = random.sample(clubs, 3)
        #args_for_response['clubs'] = clubs
        args_for_response["clubs"] = []

        # Load some birthdays
        #birthdays_users = ListBirthdays.get_today_birthdays()
        #args_for_response['birthdays_users'] = birthdays_users
        args_for_response['birthdays_users'] = []

        # Load some campus mails
        args_for_response['campus_mails'] = Mail.objects.order_by('-date').filter(moderated=True).all()[:settings.NUMBER_NEWS_IN_HOME]

        if request.user.is_authenticated:
            end_fee = request.ldap_user.end_cotiz if request.ldap_user.end_cotiz else False
            employee_type = request.ldap_user.employee_type
            args_for_response['employee_type'] = employee_type

            # Check email validation:
            user_meta = UserMetaData.objects.get_or_create(uid=request.ldap_user.uid)
            args_for_response['user_meta'] = user_meta
            # Check his end fees date
            template_for_response = self.logged_template
            args_for_response['end_fee'] = end_fee

        elif request.network_data['is_logged_in']:
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
    description = _("Des informations sur l'état du réseau sur les campus de Brest, Nantes et Rennes")

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
            services = services.get_articles_and_links(self.request.network_data['subnet'] == 'USER')
        except Category.DoesNotExist:
            services = []
        return services

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
    if (request.network_data['subnet'] not in ['EXPN', 'REGN'] or
        request.network_data['is_logged_in']):
        return HttpResponseRedirect(reverse('home'))
    return render(
        request,
        'pages/inscription_zone_info.html',
        {}
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
        service_score = 0
        lvl = service.get('level', 1)  # Default to warning
        hosts_max_score = {}

        if service.get('_hosts', None) is None:
            service['status_text'] = 'Pas de métriques'
            service['status'] = 'default'
            return -1


        for icn_service in icinga_rsp['results']:
            host = icn_service['joins']['host']['name']
            if host in service.get('_hosts', []) \
                    and icn_service['attrs']['name'] not in excl:
                hosts_max_score[host] = max(
                    hosts_max_score.get(host, 0),
                    icn_service['attrs']['state'],
                )

        if hosts_max_score:
            if service.get('_hosts_failover', False):
                service_score = min(hosts_max_score.values())
            else:
                service_score = max(hosts_max_score.values())

        StatusPageXhr.cleanup(service)
        if service_score == 0:
            service['status_text'] = 'Système nominal'
            service['status'] = 'success'
        elif service_score == 1:
            service['status_text'] = 'Incidents mineurs'
            service['status'] = 'warning'
        else:
            service['status_text'] = 'Incidents majeurs'
            service['status'] = 'danger'
        return lvl * service_score

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
                "L'accès à Internet n'est pas affecté")
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
        with open('myresel/icinga_status.yml', 'rb') as doc:
            services = yaml.safe_load(doc)
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
            with open('myresel/icinga_dummy_resp.yml', 'rb') as dummy_resp:
                result = yaml.safe_load(dummy_resp)
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


@csrf_exempt
def graph_api(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('home'))
    body = request.body.decode()
    if '!FETCH' in body and not request.user.is_authenticated:
        raise PermissionDenied()
    body = settings.WARP10_PRELUDE.format(request.user.username) + body
    try:
        resp = requests.post(url=settings.WARP10_ENDPOINT, data=body)
    except requests.exceptions.RequestException:
        return HttpResponseServerError()
    response = HttpResponse(resp.content, status=resp.status_code)
    for header in resp.headers:
        if header.lower() not in settings.IGNORED_HEADERS:
            response[header] = resp.headers[header]
    return response


@login_required
def eggdrop(request, channel=None, year=None, month=None, day=None):
    """Page with the irc logs"""

    def convert_to_html(filename):
        import io
        import irclog2html.irclog2html as irc

        try:
            infile = irc.open_log_file(filename)
        except EnvironmentError as e:
            raise Http404
        outfile = io.BytesIO()

        parser = irc.LogParser(infile)
        formatter = irc.XHTMLStyle(outfile)
        irc.convert_irc_log(parser, formatter,
                title='', prev=('', ''), index=('', ''), next=('', ''))

        outfile.seek(0)
        return outfile.read().decode('utf-8')

    if channel is None:
        requested_channel = settings.EGGDROP_DEFAULT_CHANNEL
    elif channel in [c[1] for c in settings.EGGDROP_CHANNELS]:
        requested_channel = channel
    else:
        raise Http404

    if year is None:
        requested_date_r = timezone.now()
    else:
        requested_date_r = datetime.datetime(year=int(year), month=int(month), day=int(day))

    requested_date = requested_date_r.strftime('%Y%m%d')

    log_file = os.path.join(
        settings.EGGDROP_FOLDER,
        '%s.log.%s' % (requested_channel, requested_date)
    )

    if not os.path.isfile(log_file):
        raise Http404

    logs = convert_to_html(log_file)

    return render(
        request,
        'pages/eggdrop.html', {
            'logs': logs,
            'channels': settings.EGGDROP_CHANNELS,
            'channel': { 'slug': requested_channel, 'name': ''},
            'date': requested_date_r,
            'previous': requested_date_r + datetime.timedelta(days=-1),
            'next': requested_date_r + datetime.timedelta(days=1),
        }
    )

@method_decorator(resel_required, name='dispatch')
class Television(TemplateView):
    template_name = "pages/tv.html"
