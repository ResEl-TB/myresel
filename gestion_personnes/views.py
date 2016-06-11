from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from fonctions import ldap
from .forms import *

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

# Create your views here.
class Inscription(TemplateView):
    """
    Vue appelée pour que l'user s'inscrive au ResEl
    C'est cette vue qui créer la fiche LDAP de l'user
    On lui affiche le réglement intérieur, et un formulaire pour remplir les champs LDAP
    """
    template_name = 'gestion_personnes/inscription.html'
    form_class = InscriptionForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Inscription, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # On process les données

            return 

        return render(request, self.template_name, {'form': form})