import logging
import re

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from fonctions import ldap, network

logger = logging.getLogger("default")

def resel_required(function=None, redirect_to='home'):
    """ Vérifie que l'user a une IP resel

    Ce décorateur s'assure que l'user a bien une IP ResEl.
    Si ce n'est pas le cas, il est redirigé vers l'adresse spécifiée dans
    'redirect_to', sinon vers la page de news.
    """

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if 'HTTP_X_FORWARDED_FOR' in request.META:
                ip = request.META['HTTP_X_FORWARDED_FOR']
            else:
                ip = request.META['REMOTE_ADDR']

            if network.is_resel_ip(ip):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, _("Vous devez vous trouver sur le réseau du ResEl pour accéder à cette page."))
                return HttpResponseRedirect(reverse(redirect_to))

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)


def unknown_machine(function=None, redirect_to='home'):
    """ Vérifie que la machine de l'user est inconnue.

    Ce décorateur s'assure que la machine de l'user est bien inconnue dans le LDAP.
    Si ce n'est pas le cas, il est redirigé vers l'adresse spécifiée dans
    'redirect_to', sinon vers la page de news.
    """

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            mac = network.get_mac(request.network_data['ip'])

            if ldap.search(settings.LDAP_DN_MACHINES, '(&(macaddress=%s))' % mac):
                messages.error(request, _("Votre machine est déjà connue par notre réseau. Par conséquent, vous n'avez pas besoin d'accéder à cette page."))
                return HttpResponseRedirect(reverse(redirect_to))
            else:
                return view_func(request, *args, **kwargs)

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)


def need_to_pay(function=None, redirect_to='home'):
    """ Vérifie que l'utilisateur n'a pas payé son accès Internet.

    Ce décorateur s'assure que l'utilisateur doit payer son accès Internet.
    Si ce n'est pas le cas, il est redirigé vers la page spécifiée dans 'redirect_to'
    ou à défaut vers la page de news.
    """

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            try:
                if not request.ldap_user:
                    raise AttributeError("The user is not logged in")
                if request.ldap_user.need_to_pay() == 'success':
                    messages.info(request, _("Votre cotisation et vos frais d'accès internet sont à jour."))
                    return HttpResponseRedirect(reverse(redirect_to))
            except AttributeError as e:
                logger.error("An unlogged user tried to access the trésorie module")
                return HttpResponseRedirect(reverse(redirect_to))

            return view_func(request, *args, **kwargs)
        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)


def correct_vlan(function=None, redirect_to='home'):
    """ Informe l'user de changer de vlan si sa machine est déjà inscrite.

    Ce décorateur check l'ip de l'utilisateur de le vlan depuis lequel il se connecte.
    Si ip en 224-225 et vlan 995, pas de soucis.
    Si ip en zone utilisateur mais vlan 995, informe l'user de se déco du ResEl inscription.
    """

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if 'HTTP_X_FORWARDED_FOR' in request.META:
                ip = request.META['HTTP_X_FORWARDED_FOR']
            else:
                ip = request.META['REMOTE_ADDR']

            if network.is_resel_ip(ip) and not re.match(r'^172.22.22[4-5]', ip) and request.META['VLAN'] == '995':
                messages.error(request, _("Votre machine est déjà inscrite. Veuillez vous connecter sur le réseau Wi-Fi ResEl Secure."))
                return HttpResponseRedirect(reverse(redirect_to))
            
            return view_func(request, *args, **kwargs)

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)
