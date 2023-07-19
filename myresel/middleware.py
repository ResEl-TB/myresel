# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MiddlewareNotUsed
from django.urls import resolve, Resolver404, reverse
from django.http import HttpResponseRedirect

from fonctions import ldap
from gestion_personnes.models import LdapUser

logger = logging.getLogger("default")
class IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAResElAdminSoCheckTheLdapBeforeMiddleware:
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
            user.is_authenticated and
            not (user.is_staff and user.is_superuser) and
            ldap.search(settings.LDAP_OU_ADMIN, '(&(uid=%s))' % user.username)
        )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                request.ldap_user = LdapUser.get(pk=request.user.username)
            except ObjectDoesNotExist:
                logout(request)

        if self.is_staff(request.user):
            self.make_user_staff(username=request.user.username)
        response = self.get_response(request)
        # After the request: Do nothing
        return response


class NetworkConfiguration:
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
        if 'ZONE' in request.META:
            raw_zone = request.META['ZONE'].split('-')
        else:
            raw_zone = ['EXT']
        raw_zone.append(None)
        request.network_data['ip'] = ip
        request.network_data['host'] = request.META['HTTP_HOST']
        request.network_data['zone'] = raw_zone[0]
        request.network_data['subnet'] = raw_zone[1]
        request.network_data['is_logged_in'] = request.user.is_authenticated
        request.network_data['is_resel'] = raw_zone[0] != 'EXT'

        response = self.get_response(request)
        return response

class InscriptionNetworkHandler:
    """
    Before the request is sent to the website, we need to handle if the user
    is in a registration network
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def deport(self):
        try:
            path_url = resolve(self.request.path).url_name
            path_namespaces = resolve(self.request.path).namespaces

            test_urlname = [m == path_url for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAME]
            test_urlnamespace = [m in path_namespaces for m in settings.INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE]

            if not (any(test_urlname) or any(test_urlnamespace)):
                return HttpResponseRedirect(reverse(settings.INSCRIPTION_ZONE_FALLBACK_URLNAME))
        except Resolver404:  # It's a 404
            return HttpResponseRedirect(reverse(settings.INSCRIPTION_ZONE_FALLBACK_URLNAME))
        return None

    def __call__(self, request):
        self.request = request

        #ip = request.network_data['ip']
        subnet = request.network_data['subnet']
        #host = request.network_data['host']
        #zone = request.network_data['zone']
        #is_registered = request.network_data['is_registered']
        is_logged_in = request.network_data['is_logged_in']

        if not is_logged_in and (subnet == 'EXPN' or subnet == 'REGN'):
            redirect = self.deport()
            if redirect:
                return redirect

        response = self.get_response(request)
        return response

class SimulateProductionNetwork:
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
        except KeyError:
            client_fake_ip = '10.0.0.1'
        request.META["REMOTE_ADDR"] = client_fake_ip

        response = self.get_response(request)
        return response
