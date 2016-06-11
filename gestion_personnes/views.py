from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect

from fonctions import ldap, generic
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

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            import time
            year = generic.get_year()

            # Mise en forme du DN et des attributs de la fiche LDAP
            dn = 'uid=%s,ou=people,dc=maisel,dc=enst-bretagne,dc=fr' % form.cleaned_data['pseudo']
            object_class = ['genericPerson','enstbPerson','reselPerson', 'maiselPerson']
            attributes = {
                'uid': form.cleaned_data['pseudo'],
                'firstname': form.cleaned_data['prenom'],
                'lastname': form.cleaned_data['nom'],
                'mail': form.cleaned_data['mail'],
                'anneeScolaire': '{}/{}'.format(year, year+1),
                'dateInscr': time.strftime('%Y%m%d%H%M%S') + 'Z',
                'objectClass': ['genericPerson','enstbPerson','reselPerson', 'maiselPerson'],
                'campus': generic.get_campus(request.META['HTTP_X_FORWARDED_FOR']),
                'userPassword': generic.hash_passwd(form.cleaned_data['mot_de_passe']),
                'ntPassword': generic.hash_to_ntpass(form.cleaned_data['mot_de_passe']),
                'batiment': form.cleaned_data['batiment'],
                'roomNumber': form.cleaned_data['chambre'],
                'mobile': form.cleaned_data['telephone']
            }

            # Ajout de la fiche au LDAP
            ldap.add(dn, object_class, attributes)

            # Inscription de la personne à la ML campus
            mail = EmailMessage(
                subject = "SUBSCRIBE campus {} {}".format(form.cleaned_data['prenom'], form.cleaned_data['nom']),
                body = "Inscription automatique de {} a campus".format(form.cleaned_data['pseudo']),
                from_email = form.cleaned_data['mail'],
                reply_to = ["listmaster@resel.fr"],
                to = ["sympa@resel.fr"],
            )
            mail.send()

            return HttpResponseRedirect(""" Insérer lien de redirection ici """)

        return render(request, self.template_name, {'form': form})