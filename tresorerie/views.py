from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

# Create your views here.
class Home(TemplateView):
    """ Vue index de la section paiement. C'est cette page qui gère le paiement d'un user
        La page contient un formulaire qui contacte admin.r.f pour le paiement via Stripe.
     """

    template_name = 'paiement/home.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

class Historique(View):
    """ Vue qui affiche un historique des paiements de l'uitlisateur """

    template_name = 'paiement/historique.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Historique, self).dispatch(*args, **kwargs)