from django.shortcuts import render
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

from fonctions import ldap, generic, network
from fonctions.decorators import resel_required, unknown_machine
from .forms import InscriptionForm, ModPasswdForm
from ldap3 import MODIFY_REPLACE

from django.utils.translation import ugettext_lazy as _


class Inscription(View):
    """
    Vue appelée pour que l'user s'inscrive au ResEl
    C'est cette vue qui créer la fiche LDAP de l'user
    On lui affiche le réglement intérieur, et un formulaire pour remplir les champs LDAP
    """
    template_name = 'gestion_personnes/inscription.html'
    form_class = InscriptionForm

    @method_decorator(resel_required)
    @method_decorator(unknown_machine)
    def dispatch(self, *args, **kwargs):
        return super(Inscription, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            import time
            year = generic.get_year()

            # Mise en forme du DN et des attributs de la fiche LDAP
            dn = 'uid=%s,ou=people,dc=maisel,dc=enst-bretagne,dc=fr' % form.cleaned_data["username"].lower()
            object_class = ['genericPerson','enstbPerson','reselPerson', 'maiselPerson']
            attributes = {
                # Attributs genericPerson
                'uid': form.cleaned_data["username"].lower(),
                'firstname': form.cleaned_data["first_name"],
                'lastname': form.cleaned_data["last_name"],
                'displayname': form.cleaned_data["first_name"] + ' ' + form.cleaned_data["last_name"],
                'userPassword': generic.hash_passwd(form.cleaned_data["password"]),
                'ntPassword': generic.hash_to_ntpass(form.cleaned_data["password"]),

                # enstbPerson
                'promo': str(year + 3),
                'mail': form.cleaned_data["email"],
                'anneeScolaire': '{}/{}'.format(year, year+1),
                'mobile': form.cleaned_data["phone"],
                'option': network.get_campus(request.META['REMOTE_HOST']),

                # reselPerson
                'dateInscr': time.strftime('%Y%m%d%H%M%S') + 'Z',
                'cotiz': 'BLACKLIST' + str(year),
                'endCotiz': time.strftime('%Y%m%d%H%M%S') + 'Z',

                # maiselPerson
                'campus': network.get_campus(request.META['REMOTE_HOST']),
                'batiment': 'I' + form.cleaned_data["building"],
                'roomNumber': str(form.cleaned_data["room"]),
            }

            # Ajout de la fiche au LDAP
            ldap.add(dn, object_class, attributes)

            # Inscription de la personne à la ML campus
            mail = EmailMessage(
                subject = "SUBSCRIBE campus {} {}".format(form.cleaned_data["first_name"], form.cleaned_data["last_name"]),
                body = "Inscription automatique de {} a campus".format(form.cleaned_data["username"]),
                from_email = form.cleaned_data["email"],
                reply_to = ["listmaster@resel.fr"],
                to = ["sympa@resel.fr"],
            )
            mail.send()

            messages.success(request, _("Vous êtes désormais inscrit au ResEl. Vous pouvez dès à présent inscrire votre machine."))
            return HttpResponseRedirect(reverse('home'))

        return render(request, self.template_name, {'form': form})


class ModPasswd(View):
    template_name = 'gestion_personnes/mod-passwd.html'
    form_class = ModPasswdForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ModPasswd, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid:
            print(form)
            dn = 'uid=%s,' % request.user + settings.LDAP_DN_PEOPLE
            modifs = {
                'userpassword': [(MODIFY_REPLACE, [generic.hash_passwd(form.cleaned_data["password"])])],
                'ntpassword': [(MODIFY_REPLACE, [generic.hash_to_ntpass(form.cleaned_data["password"])])],
            }
            ldap.modify(dn, modifs)

            messages.success(request, _("Votre mot de passe a été modifié"))
            return HttpResponseRedirect(reverse('home'))

        return render(request, self.template_name, {'form': form})