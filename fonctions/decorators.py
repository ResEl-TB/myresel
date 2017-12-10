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
from django.db.utils import OperationalError
from django.core.cache import cache

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
                messages.error(request, _('Vous n\'êtes pas membre de l\'AE, vous ne pouvez donc pas réserver de salle'))
                return HttpResponseRedirect(reverse(redirect_to))

            return view_func(request, *args, **kwargs)
        return _view

    return _dec(function)

#################################################
#
# Tools for the robust_cache
#
#################################################


# The following code is under the Python Foundation License:
#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
# 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017
# Python Software Foundation. All rights reserved.


class _HashedSeq(list):
    """ This class guarantees that hash() will be called no more than once
        per element.  This is important because the lru_cache() will hash
        the key multiple times on a cache miss.
    """

    __slots__ = 'hashvalue'

    def __init__(self, tup, hash=hash):
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self):
        return self.hashvalue

def _make_key(args, kwds, typed,
             kwd_mark = (object(),),
             fasttypes = {int, str, frozenset, type(None)},
             tuple=tuple, type=type, len=len):
    """Make a cache key from optionally typed positional and keyword arguments
    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.
    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.
    """
    # All of code below relies on kwds preserving the order input by the user.
    # Formerly, we sorted() the kwds before looping.  The new way is *much*
    # faster; however, it means that f(x=1, y=2) will now be treated as a
    # distinct call from f(y=2, x=1) which will be cached separately.
    key = args
    if kwds:
        key += kwd_mark
        for item in kwds.items():
            key += item
    if typed:
        key += tuple(type(v) for v in args)
        if kwds:
            key += tuple(type(v) for v in kwds.values())
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)

############################################
#
# Robust cache functions
# "ResEl license"
#
############################################


class LongCacheMissException(Exception):
    pass

def robust_cache(short_timeout=300, long_timeout=604800, exp=(OperationalError,)):
    """
    Load and save data from cache

    This cache is like a simple lru cache, but is a bit smarter because of
    ResEl constrains: Unreliable network...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            result = None
            func_key = '%s.%s:%s' % (
                func.__module__,
                func.__name__,
                _make_key(args, kwds, typed=False)
            )

            short_cache_key = 's_%s' % func_key
            long_cache_key = 'l_%s' % func_key

            # 1. fetch from short cache:
            result = cache.get(short_cache_key)

            print(result)
            if result is not None:
                return result

            # 2. fetch from function
            try:
                result = func(*args, **kwds)

                # save in both caches
                cache.set(short_cache_key, result, short_timeout)
                cache.set(long_cache_key, result, long_timeout)
                return result

            except exp as e:
                logger.warning(
                    "cached function called raised an exception: %s - %s" % (
                        func_key, e),
                    extra={
                        "function": '%s.%s:%s' % (
                            func.__module__,
                            func.__name__,
                            e),
                        "exception": str(e),
                        'message_code': 'EXCEPTION_CALLING_CACHED_FUNC',
                    }
                )
                # 3. fecth from long cache
                result = cache.get(long_cache_key)
                if result is None:
                   raise LongCacheMissException('Function call result no where')
            return result
        return wrapper
    return decorator
