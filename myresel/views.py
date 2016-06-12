from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from fonctions import ldap

# Create your views here.
class Home(TemplateView):
    """ Vue d'index, qui se charge de rediriger l'utilisateur sur la bonne page """
    template_name = 'myresel/home.html'

    def get(self, request, *args, **kwargs):
        # On vérifie que la machine n'est pas desactivée.
        # Si oui, on bascule vers la page de réactivation
        status = ldap.get_status(request.META['HTTP_X_FORWARDED_FOR'])

        if status:
            # La machine existe dans le LDAP
            if status == 'inactive':
                # La machine est inactive
                return HttpRespondeRedirect(reverse('gestion_machines:reactivation'))

            elif status == 'mauvais_campus':
                # La machine n'est pas dans le bon campus
                return HttpRespondeRedirect(reverse('gestion_machines:changement-campus'))

            else:
                # La machine est active, on affiche la page d'accueil traditionnelle
                return render(self.template_name)

        # La machine n'existe pas dans le LDAP, on renvoit vers la page d'ajout de machine
        return HttpRespondeRedirect(reverse('gestion_machines:ajout'))