# -*- coding: utf-8 -*-
import logging

from htmlvalidator.middleware import HTMLValidator as HTMLValidatorParent
from django.utils.deprecation import MiddlewareMixin

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MiddlewareNotUsed
from django.core.urlresolvers import resolve, Resolver404, reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from fonctions import ldap, network
from gestion_personnes.models import LdapUser

logger = logging.getLogger("default")
class IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAResElAdminSoCheckTheLdapBeforeMiddleware(object):
    @staticmethod
    def make_user_staff(username):
        """
        Save in Django database if a user is part of the staff
        :param username:
        :return:
        """
        user = User.objects.get(username=username)
        user.is_staff = 1
        user.is_superuser = 1
        user.save()

    @staticmethod
    def is_staff(user):
        """
        Tells if a DjangoUser is part of RENAS
        :param user: DjangoUser
        :return: bool
        """
        # TODO: move this code to the new backend
        return (
            user.is_authenticated() and
            not (user.is_staff and user.is_superuser) and
            ldap.search(settings.LDAP_OU_ADMIN, '(&(uid=%s))' % user.username)
        )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated():
            try:
                request.ldap_user = LdapUser.get(pk=request.user.username)
            except ObjectDoesNotExist:
                logout(request)

        if self.is_staff(request.user):
            self.make_user_staff(username=request.user.username)
        response = self.get_response(request)
        # After the request: Do nothing
        return response


class NetworkConfiguration(object):
    """
    Retrieve every useful piece of information about the device network configuration
    To be available in every view
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.network_data = {}
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
        ip = ip.split(' ')[-1]  # HOT fix to handle some bugs during port fowarding
        ip_suffix = ip.split(".")[2:]
        zone = network.get_network_zone(ip)
        request.network_data['ip'] = ip
        request.network_data['ip_suffix'] = ip_suffix
        request.network_data['vlan'] = request.META['VLAN']
        request.network_data['host'] = request.META['HTTP_HOST']
        request.network_data['zone'] = zone
        request.network_data['is_registered'] = 'unknown'
        request.network_data['is_logged_in'] = request.user.is_authenticated()
        request.network_data['is_resel'] = network.is_resel_ip(ip)

        # If the device in `user` or `inscription` zone, we can retrieve its mac address
        if "user" in zone or "inscription" in zone:
            # Hack to redirect to the good campus
            if network.get_campus(ip) == "Rennes" and settings.CURRENT_CAMPUS == "Brest":
                return HttpResponseRedirect("https://" + settings.MAIN_HOST_RENNES + request.get_full_path())
            elif network.get_campus(ip) == "Brest" and settings.CURRENT_CAMPUS == "Rennes":
                return HttpResponseRedirect("https://" + settings.MAIN_HOST_BREST + request.get_full_path())

            request.network_data['is_registered'] = ldap.get_status(ip)  # TODO: possible bug

        response = self.get_response(request)
        return response

class InscriptionNetworkHandler(object):
    """
    Before the request is sent to the website, we need to handle if the user
    is in an inscription network
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def deport(self):
        """
        Force the user into the inscription zone
        Only the urls set in `settings.INSCRIPTION_ZONE_ALLOWED_URLNAME` and
        `settings.INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE`
        And deport him into : `settings.INSCRIPTION_ZONE_FALLBACK_URLNAME`

        :return HttpResponseRedirect if necessary, None if nothing to do
        """
        # Check if logged in & registered
        # We check that he only browses intended part of the website
        try:
            path_url = resolve(self.request.path).url_name
            path_namespaces = resolve(self.request.path).namespaces

            test_urlname = [m == path_url for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAME]
            test_urlnamespace = [m in path_namespaces for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE]

            if not (any(test_urlname) or any(test_urlnamespace)):
                return HttpResponseRedirect(reverse(settings.INSCRIPTION_ZONE_FALLBACK_URLNAME))

        # If it is a 404, it is very likely that it is because the browser
        # tried to open a tab in order to test the  connection. The best
        # solution is to redirect the user to the landing page.
        except Resolver404:  # It's a 404
            return HttpResponseRedirect(reverse(settings.INSCRIPTION_ZONE_FALLBACK_URLNAME))
        return None

    def __call__(self, request):
        """
        We need to check two things:
        1. If the user is in vlan inscription (995):
         * He browse any non-resel page (but the DNS server sends him to r.f):
           -> He is sent to an informative page that tell him either to subscribe/activate his device
               if his device is unknown, either change WLAN if his device is registered.
         * He browse the ResEl:
           + He is logged in & his device is registered:
               -> Let him access the website but send a warning that he needs to log on the other network
           + He isn't logged in / His device isn't registered:
              -> Let him access only the homepage the login page, and the activation page

        2. If the user is in vlan user (999):
           * If the device's IP is in user subnet:
             -> Ok
          * device's IP is in inscription-999 subnet:
            -> Same as 1 except if his device is registered, we tell him to plug/unplug ethernet jack or
               disconnect/reconnect to Wifi
        """
        self.request = request

        # First get device datas
        ip = request.network_data['ip']
        vlan = request.network_data['vlan']
        host = request.network_data['host']
        zone = request.network_data['zone']
        is_registered = request.network_data['is_registered']
        is_logged_in = request.network_data['is_logged_in']

        # Vlan inscription
        if vlan == '995':
            # Preliminary check

            if 'inscription' not in zone:
                logger.warning("IP et VLAN non concordants"
                             "\n IP : %s"
                             "\n HOST : %s"
                             "\n ZONE : %s"
                             "\n VLAN : %s"
                             "\n Utilisateur : %s"
                             "\n Machine : %s"
                             % (ip, host, zone, vlan, is_logged_in, is_registered),
                             extra={
                                 "device_ip": ip,
                                 "device_hostname": host,
                                 "device_zone": zone,
                                 "device_vlan": vlan,
                                 "user": is_logged_in
                             })

                # Error ! In vlan 995 without inscription IP address
                return HttpResponseBadRequest(_("Vous vous trouvez sur un réseau d'inscription mais ne possédez pas d'IP dans ce réseau. Veuillez contacter un administrateur."))

            else:
                redirect = self.deport()
                if redirect:
                    return redirect

        elif vlan == '999':
            if zone == 'internet':
                # Error ! Zone internet shouldn't be on vlan 999 !
                return HttpResponseBadRequest(_("Une erreur s'est glissée dans le traitement de votre requête. Si le problème persiste, contactez un administrateur."))

            elif (zone == 'Brest-user' or zone == 'Rennes-user') and is_registered == 'unknown':
                # Check if the device is in the LDAP, if no put him in the
                # inscription zone.
                # This is new from 2017-05-04, see : https://git.resel.fr/resel/general/issues/1
                redirect = self.deport()
                if redirect:
                    return redirect

            elif zone == 'Brest-inscription-999' or zone == 'Rennes-inscription-999':
                redirect = self.deport()
                if redirect:
                    return redirect

            else:
                # Other possiblities: Brest-inscription, Brest-other.
                # Should never happen... but ?
                pass

        response = self.get_response(request)
        return response


class SimulateProductionNetwork(object):
    """
    Simulate a production environment for the Vagrant env
    This is because the ResEl is hard
    """
    def __init__(self, get_response):
        if not (settings.DEBUG or settings.TESTING):
            raise MiddlewareNotUsed("Only used in developement environment")
        self.get_response = get_response

    def __call__(self, request):
        host = request.META["HTTP_HOST"].split(":")[0]

        try:
            client_fake_ip = settings.DEBUG_SETTINGS['networks'][host]['client_fake_ip']
            client_fake_vlan = settings.DEBUG_SETTINGS['networks'][host]['vlan']
        except KeyError:
            client_fake_ip = '10.0.0.1'
            client_fake_vlan = '994'
        request.META["REMOTE_ADDR"] = client_fake_ip
        request.META['VLAN'] = client_fake_vlan

        response = self.get_response(request)
        return response


class HTMLValidator(HTMLValidatorParent, MiddlewareMixin):
    pass
