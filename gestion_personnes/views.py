import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from ldap3 import MODIFY_REPLACE

from fonctions import ldap, generic, network
from fonctions.decorators import resel_required, unknown_machine
from gestion_personnes.models import LdapUser
from .forms import InscriptionForm, ModPasswdForm


class Inscription(View):
    """
    Vue appelée pour que l'user s'inscrive au ResEl
    C'est cette vue qui créer la fiche LDAP de l'user
    On lui affiche le réglement intérieur, et un formulaire pour remplir les champs LDAP
    """
    # TODO: gestion des batiments de Rennes
    # Ne plus laisser le choix de l'uid pour l'utilisateur (afficher une page avec la confirmation
    # Envoyer un email à l'utilisateur
    # Refactoriser la création de l'utilsateur ailleurs
    # Choix de la promo

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
            current_year = generic.current_year()

            user = LdapUser()
            user.uid = form.cleaned_data["username"].lower()
            user.firstname = form.cleaned_data["first_name"]
            user.lastname = form.cleaned_data["last_name"]
            user.displayname = form.cleaned_data["first_name"] + ' ' + form.cleaned_data["last_name"]
            user.userPassword = generic.hash_passwd(form.cleaned_data["password"])
            user.ntPassword = generic.hash_to_ntpass(form.cleaned_data["password"])

            user.promo = str(current_year + 3)
            user.mail = form.cleaned_data["email"]
            user.anneeScolaire = form.cleaned_data["email"]
            user.mobile = form.cleaned_data["phone"]
            user.option = network.get_campus(request.META['REMOTE_HOST'])

            user.dateInscr = time.strftime('%Y%m%d%H%M%S') + 'Z'
            user.cotiz = 'BLACKLIST' + str(current_year)
            user.endCotiz = time.strftime('%Y%m%d%H%M%S') + 'Z'

            user.campus = network.get_campus(request.META['REMOTE_HOST'])
            user.batiment = 'I' + form.cleaned_data["building"]
            user.roomNumber = str(form.cleaned_data["room"])

            user.save()

            # Inscription de la personne à la ML campus
            mail = EmailMessage(
                subject="SUBSCRIBE campus {} {}".format(form.cleaned_data["first_name"], form.cleaned_data["last_name"]),
                body="Inscription automatique de {} a campus".format(form.cleaned_data["username"]),
                from_email=form.cleaned_data["email"],
                reply_to=["listmaster@resel.fr"],
                to=["sympa@resel.fr"],
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