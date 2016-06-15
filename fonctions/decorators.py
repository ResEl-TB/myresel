from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

from .network import is_resel_ip, get_mac
from .ldap import search
from myresel.constantes import DN_MACHINES, DN_PEOPLE
from datetime import datetime

def resel_required(function = None, redirect_to = 'news'):
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

            if is_resel_ip(ip):
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

def unknown_machine(function = None, redirect_to = 'news'):
    """ Vérifie que la machine de l'user est inconnue.

    Ce décorateur s'assure que la machine de l'user est bien inconnue dans le LDAP.
    Si ce n'est pas le cas, il est redirigé vers l'adresse spécifiée dans
    'redirect_to', sinon vers la page de news.
    """

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            mac = get_mac(request.META['REMOTE_ADDR'])

            if search(DN_MACHINES, '(&(macaddress=%s))' % mac):
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

def need_to_pay(function = None, redirect_to = 'news'):
    """ Vérifie que l'utilisateur n'a pas payé son accès Internet.

    Ce décorateur s'assure que l'utilisateur doit payer son accès Internet.
    Si ce n'est pas le cas, il est redirigé vers la page spécifiée dans 'redirect_to'
    ou à défaut vers la page de news.
    """

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            user = search(DN_PEOPLE, '(&(uid=%s))' % request.user, ['cotiz', 'endinternet'])[0]
            if 'cotiz' in user.entry_to_json().lower() and 'endinternet' in user.entry_to_json().lower():
                end_date = datetime.strptime(user.endinternet[0], '%d/%m/%Y')
                if end_date > datetime.now():
                    # Cotisation déjà payée
                    messages.info(_("Vous avez déjà payé votre cotisation."))
                    return HttpResponseRedirect(reverse('news'))
                else:
                    return view_func(request, *args, **kwargs)
            else:
                return view_func(request, *args, **kwargs)

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view