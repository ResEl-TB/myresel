from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.core.urlresolvers import resolve, Resolver404, reverse

from fonctions import ldap, network
from gestion_machines.models import LdapDevice


class IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAResElAdminSoCheckTheLdapBeforeMiddleware(object):
    def process_request(self, request):
        # Check if the user is a ResEl admin. If so, its credentials will be updated to superuser and staff
        if request.user.is_authenticated() and not (request.user.is_staff and request.user.is_superuser):
            res = ldap.search(settings.LDAP_DN_ADMIN, '(&(uid=%s))' % request.user.username)
            if res:
                user = User.objects.get(username=request.user.username)
                user.is_staff = 1
                user.is_superuser = 1
                user.save()


class NetworkConfiguration(object):
    """
    Retrieve every useful piece of information about the device network configuration
    To be available in every view
    """
    def process_request(self, request):
        request.network_data = {}
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
        zone = network.get_network_zone(ip)
        request.network_data['ip'] = ip
        request.network_data['vlan'] = request.META['VLAN']
        request.network_data['host'] = request.META['HTTP_HOST']
        request.network_data['zone'] = zone
        request.network_data['mac'] = None
        request.network_data['is_registered'] = 'unknown'
        request.network_data['is_logged_in'] = request.user.is_authenticated()
        request.network_data['is_resel'] = network.is_resel_ip(ip)

        # If the device in `user` or `inscription` zone, we can retrieve its mac address
        if "user" in zone or "inscription" in zone:
            request.network_data['mac'] = network.get_mac(ip)
            request.network_data['is_registered'] = ldap.get_status(ip)  # TODO: possible bug

            if not request.network_data['mac']:
                # Error ! couldn't get its mac address
                return HttpResponseBadRequest(_("Impossible de détecter votre adresse mac, veuillez contacter un administrateur ResEl."))

        if request.network_data['is_registered'] != 'unknown':
            end_ip = ".".join(ip.split(".")[-2:])
            current_device = LdapDevice.get(mac_address=request.network_data['mac'])
            request.network_data['device'] = current_device


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
        ip = request.network_data['ip']
        vlan = request.network_data['vlan']
        host = request.network_data['host']
        zone = request.network_data['zone']
        mac = request.network_data['mac']
        is_registered = request.network_data['is_registered']
        is_logged_in = request.network_data['is_logged_in']

        # Vlan inscription
        if vlan == '995':

            # Preliminary check

            if zone != 'Brest-inscription':
                # Error ! In vlan 995 without inscription IP address
                return HttpResponseBadRequest(_("Vous vous trouvez sur un réseau d'inscription mais ne possédez pas d'IP dans ce réseau. Veuillez contacter un administrateur."))

            # Check origin:
            # if host not in settings.ALLOWED_HOSTS:
            #     return HttpResponseRedirect(settings.INSCRIPTION_ZONE_FALLBACK_URL)  # Will bypass the normal view

            else:
                # Check if logged in & registered:
                if is_registered == 'active' and is_logged_in:
                    messages.warning(request, _("Vous êtes correctement inscrit, mais vous êtes sur le mauvais réseau. Veuillez vous connecter sur le réseau Wifi 'ResEl Secure'"))

                else:
                    # We check that he only browses intended part of the website
                    try:
                        path_url = resolve(request.path).url_name
                        path_namespaces = resolve(request.path).namespaces

                        test_urlname = [m == path_url for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAME]
                        test_urlnamespace = [m in path_namespaces for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE]

                        if not (any(test_urlname) or any(test_urlnamespace)):
                            messages.info(request, _("Vous devez vous inscrire au ResEl avant de pouvoir naviguer normalement."))
                            return HttpResponseRedirect(settings.LOGIN_URL)

                    # If it is a 404, it is very likely that it is because the
                    # browser tried to open a tab in order to test the
                    # connection. The best solution is to redirect the user to
                    # the landing page.
                    except Resolver404:  # It's a 404
                        return HttpResponseRedirect(reverse(settings.INSCRIPTION_ZONE_FALLBACK_URLNAME))

        elif vlan == '999':

            if zone == 'internet':
                # Error ! Zone internet shouldn't be on vlan 999 !
                return HttpResponseBadRequest(_("Une erreur s'est glissée dans le traitement de votre requête. Si le problème persiste, contactez un administrateur."))

            elif zone == 'Brest-user' or zone == 'Rennes-user':
                # He can browse normally
                # pass here, so the else block don't stuck normal user.
                pass

            elif zone == 'Brest-inscription-999' or zone == 'Rennes-inscription':
                # Check origin:
                # if host not in settings.ALLOWED_HOSTS:
                #     return HttpResponseRedirect(settings.INSCRIPTION_ZONE_FALLBACK_URL)  # Will bypass the normal view
                # else:
                # Check if logged in & registered:
                if is_registered == 'active' and is_logged_in:
                    messages.warning(request, _("Votre inscription n'est pas finie. Veuillez vous déconnecter puis vous reconnecter sur le réseau Wifi 'ResEl Secure'"))
                
                else:
                    # We check that he only browses intended part of the website
                    try:
                        path_url = resolve(request.path).url_name
                        path_namespaces = resolve(request.path).namespaces

                        test_urlname = [m == path_url for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAME]
                        test_urlnamespace = [m in path_namespaces for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE]

                        if not (any(test_urlname) or any(test_urlnamespace)):
                            messages.info(request, _("Vous devez vous inscrire au ResEl avant de pouvoir naviguer normalement."))
                            return HttpResponseRedirect(settings.LOGIN_URL)

                    # If it is a 404, it is very likely that it is because the
                    # browser tried to open a tab in order to test the
                    # connection. The best solution is to redirect the user to
                    # the landing page.
                    except Resolver404:  # It's a 404
                        return HttpResponseRedirect(reverse(settings.INSCRIPTION_ZONE_FALLBACK_URLNAME))
            else:
                # Other possiblities: Brest-inscription, Brest-other.
                # Should never happen... but ?
                pass


class SimulateProductionNetwork(object):

    @staticmethod
    def process_request(request):

        if not settings.DEBUG:
            return

        host = request.META["HTTP_HOST"].split(":")[0]

        try:
            client_fake_ip = settings.DEBUG_SETTINGS['networks'][host]['client_fake_ip']
            client_fake_vlan = settings.DEBUG_SETTINGS['networks'][host]['vlan']
        except KeyError:
            client_fake_ip = '10.0.0.1'
            client_fake_vlan = '994'
        request.META["REMOTE_ADDR"] = client_fake_ip
        request.META['VLAN'] = client_fake_vlan
