# -*- coding: utf-8 -*-
import logging

from ldap3 import LDAPSocketOpenError
from django.conf import settings
from django.contrib import messages
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
        request.network_data['host'] = request.META['HTTP_HOST']
        request.network_data['zone'] = zone
        request.network_data['is_registered'] = 'unknown'
        request.network_data['is_logged_in'] = request.user.is_authenticated()
        request.network_data['is_resel'] = network.is_resel_ip(ip)

        # If the device in `user` or `inscription` zone, we can retrieve its mac address
        if "user" in zone or "inscription" in zone:
            try:
                 request.network_data['is_registered'] = ldap.get_status(ip)  # TODO: possible bug
            except LDAPSocketOpenError:
                request.network_data['is_registered'] = True
                messages.error(request, 'Base de données non joignable. Certaines fonctionnalités ne fonctionneront pas')
                logger.error(
                    "LDAP Unavailable",
                    extra={'message_code': 'LDAP_CONNECTION_ERROR'},
                )

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
        except KeyError:
            client_fake_ip = '10.0.0.1'
        request.META["REMOTE_ADDR"] = client_fake_ip

        response = self.get_response(request)
        return response
