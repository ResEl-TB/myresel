from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from fonctions import ldap, network

import re

class IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAReselAdminSoCheckTheLdapBeforeMiddleaware(object):
    def process_request(self, request):
        # Check if the user is a ResEl admin. If so, its credentials will be updated to superuser and staff
        if request.user.is_authenticated() and not (request.user.is_staff and request.user.is_superuser):
            res = ldap.search(settings.LDAP_ADMIN, '(&(uid=%s))' % request.user.username)
            if res:
                user = User.objects.get(username=request.user.username)
                user.is_staff = 1
                user.is_superuser = 1
                user.save()


class getAndCheckUsersNetworkData(object):
    """
    Centralize and check network data of user.
    """
    def process_request(self, request):
        # Get
        request.network_data = []
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            request.network_data.ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            request.network_data.ip = request.META['REMOTE_ADDR']
        request.network_data.vlan = request.META['VLAN']
        request.network_data.host = request.META['HTTP_HOST']
        request.network_data.zone = network.get_network_zone(ip)
        request.network_data.mac = False
        request.network_data.is_registered = 'Unknown'
        request.network_data.is_logged_in = request.user.is_authenticated()
        if "user" in request.network_data.zone or "inscription" in request.network_data.zone: # As the device is in an inscription or user zone, we can get its mac address
            request.network_data.mac = network.get_mac(ip)
            request.network_data.is_registered = ldap.get_status(ip)
        
        # Check
        if "user" in request.network_data.zone or "inscription" in request.network_data.zone:
            if not mac:
                # TODO: error ! couldn't have its mac address
                pass


class inscriptionNetworkHandler(object):
    # Before the request is sent to the website, we need to handle if the user is in an inscription network
    def process_request(self, request):

        # We need to check two things:
        # 1. If the user is in vlan inscription (995):
        #  * He browse any non-resel page (but the DNS server sends him to r.f):
        #    -> He is sent to an informative page that tell him either to subscribe/activate his device
        #        if his device is unknown, either change WLAN if his device is registered.
        #  * He browse the ResEl:
        #    + He is logged in & his device is registered:
        #        -> Let him access the website but send a warning that he needs to log on the other network
        #    + He isn't logged in / His device isn't registered:
        #       -> Let him access only the homepage the login page, and the activation page
        #
        # 2. If the user is in vlan user (999):
        #    * If the device's IP is in user subnet:
        #      -> Ok
        #   * device's IP is in inscription-999 subnet:
        #     -> Same as 1 except if his device is registered, we tell him to plug/unplug ethernet jack or 
        #        disconnect/reconnect to Wifi

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
        if "user" in zone or "inscription" in zone: # As the device is in an inscription or user zone, we can get its mac address
            mac = network.get_mac(ip)
            is_registered = ldap.get_status(ip)

        # Compile allowed URLs in inscription area
        INSCRIPTION_ZONE_ALLOWED_URLS = [re.compile(expr) for expr in settings.INSCRIPTION_ZONE_ALLOWED_URLS]

        # Vlan inscription
        if vlan == '995':

            # Preliminary check

            if zone != 'Brest-inscription':
                # TODO: error ! In vlan 995 without inscription IP address
                pass

            # Check origin:
            if host not in settings.ALLOWED_HOSTS:
                return HttpResponseRedirect(settings.INSCRIPTION_ZONE_FALLBACK_URL) # Will bypass the normal view

            else:
                # Check if logged in & registered:
                if is_registered == 'active' and is_logged_in:
                    messages.warning(request, _("Vous êtes correctement inscrit, mais vous êtes sur le mauvais réseau. Veuillez vous connecter sur le réseau Wifi 'ResEl Secure'"))
                else:
                    # We check that he only browses intended part of the website
                    path = request.path_info.lstrip('/')
                    if not any(m.match(path) for m in INSCRIPTION_ZONE_ALLOWED_URLS):
                        messages.info(request, _("Vous devez vous inscrire au ResEl avant de pouvoir naviguer normalement."))
                        return HttpResponseRedirect(settings.LOGIN_URL)

        elif vlan == '999':

            if zone == 'Brest-user' or zone == 'Rennes-user' or zone == 'internet':
                # TODO: zone internet shouldn't be on vlan 999 !
                # Everything is fine
                pass

            elif zone == 'Brest-inscription-999' or zone == 'Rennes-inscription':
                # Check origin:
                if host not in settings.ALLOWED_HOSTS:
                    return HttpResponseRedirect(settings.INSCRIPTION_ZONE_FALLBACK_URL) # Will bypass the normal view
                else:
                    # Check if logged in & registered:
                    if is_registered == 'active' and is_logged_in:
                        # TODO:
                        messages.warning(request, _("Votre inscription n'est pas finie. Veuillez vous déconnecter puis vous reconnecter sur le réseau Wifi 'ResEl Secure'"))
                        pass
                    else:
                        # We check that he only browses intended part of the website
                        path = request.path_info.lstrip('/')
                        if not any(m.match(path) for m in INSCRIPTION_ZONE_ALLOWED_URLS):
                            messages.info(request, _("Vous devez vous inscrire au ResEl avant de pouvoir naviguer normalement."))
                            return HttpResponseRedirect(settings.LOGIN_URL)

            else:
                # Other possiblities: Brest-inscription, Brest-other.
                # Should never happen... but ?
                pass
