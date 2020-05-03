import logging
import re
from datetime import datetime
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
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
            if request.network_data['is_resel']:
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

def ae_required(function, redirect_to='campus:rooms:calendar'):
    """
    Checks if the user is a valid ae member
    """

    def _dec(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _view(request, *args, **kwargs):
            ae = False
            for period in request.ldap_user.dates_membre:
                [start, end] = list(map(lambda x: datetime.strptime(x, '%Y%m%d').date(), period.split('-')))
                if start <= datetime.now().date() <= end:
                    ae = True
                    break

            if not ae:
                messages.error(request, _('Vous n\'êtes pas membre de l\'AE, vous ne pouvez donc pas accéder à cette page.'))
                return HttpResponseRedirect(reverse(redirect_to))

            return view_func(request, *args, **kwargs)
        return _view

    return _dec(function)

def ae_admin_required(function, redirect_to='campus:home'):
    """
    Check if the user has ae_admin attribute
    """
    def _dec(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _view(request, *args, **kwargs):
            if (not request.user.is_authenticated):
                return HttpResponseRedirect(
                    reverse("login")+"?next="+request.path
                )

            if (not request.ldap_user.ae_admin) and (not request.user.is_staff):
                messages.error(request, _('Vous n\'êtes pas admin de l\'AE.'))
                return HttpResponseRedirect(reverse(redirect_to))

            return view_func(request, *args, **kwargs)
        return _view
    return _dec(function)


def bypass_authentication(view_func):
    """ Désactive l'authentification pour une requête

    Ce décorateur permet le chargement rapide sans authentification des pages
    pour lesquelles le site agit comme un reverse proxy.
    """

    def _dec(*args, **kwargs):
        return view_func(*args, **kwargs)

    _dec._bypass_authentication = True
    return _dec
