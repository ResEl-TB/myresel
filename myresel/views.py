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
        status = ldap.get_status(request.META['REMOTE_ADDR'])

        if status:
            # La machine existe dans le LDAP
            if status == 'inactive':
                # La machine est inactive
                return HttpRespondeRedirect(reverse('gestion_machines:reactivation'))

            elif status == 'mauvais_campus':
                # La machine n'est pas dans le bon campus
                return HttpRespondeRedirect(reverse('gestion_machines:changement-campus'))

            else:
                # La machine est active, on affiche la page de news
                return HttpRespondeRedirect(reverse('news'))

        """ La machine n'existe pas dans le LDAP, donc deux cas de figure :
            - l'utilisateur est nouveau, dans ce cas il faut l'ajouter
            - la machine est inconnue

            La page affichée permet à l'utilisateur de choisir s'il doit s'inscrire lui ou sa machine
        """
        return render(request, self.template_name)

class News(TemplateView):
    """ Vue appelée pour afficher les news au niveau du ResEl """

    template_name = 'myresel/news.html'