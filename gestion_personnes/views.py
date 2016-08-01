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
from myresel.settings import SERVER_EMAIL
from .forms import InscriptionForm, ModPasswdForm, CGUForm


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

    # @method_decorator(resel_required)
    # @method_decorator(unknown_machine)
    def dispatch(self, *args, **kwargs):
        return super(Inscription, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.to_ldap_user()
            request.session['logup_ldap_user'] = user
            return HttpResponseRedirect(reverse('gestion-personnes:cgu'))

        return render(request, self.template_name, {'form': form})


class InscriptionCGU(View):
    """
    View called once the user has filled the forms
    He now has to accept the rules.
    """

    cgu_template = 'gestion_personnes/cgu.html'
    finalize_template = 'gestion_personnes/finalize_signup.html'
    form_class = CGUForm

    # @method_decorator(resel_required)
    # @method_decorator(unknown_machine)
    def get(self, request, *args, **kwargs):
        if not self.request.session['logup_ldap_user']:
            return HttpResponseRedirect(reverse('gestion-personnes:inscription'))

        form = self.form_class()
        return render(self.request, self.cgu_template, {'form': form})

    def post(self, request, *args, **kwargs):
        if not self.request.session['logup_ldap_user']:
            return HttpResponseRedirect(reverse('gestion-personnes:inscription'))

        form = self.form_class(request.POST)
        if form.is_valid():
            user = self.request.session['logup_ldap_user']
            user.save()

            # Subscribe to campus@resel.fr
            campus_email = EmailMessage(
                subject="SUBSCRIBE campus {} {}".format(user.firstname,
                                                        user.lastname),
                body="Inscription automatique de {} a campus".format(user.username),
                from_email=user.email,
                reply_to=["listmaster@resel.fr"],
                to=["sympa@resel.fr"],
            )

            # Send a validation email to the user
            # TODO: rédiger un peu plus ce mail et le faire valider par le respons' com
            # TODO: ajouter un email pour faire valider l'adresse email
            user_email = EmailMessage(
                subject=_("Inscription au ResEl"),
                body=_("Bonjour,") +
                _("\nVous êtes désormais inscrit au ResEl, voici vos identifiants :") +
                _("\nNom d'utilisateur : ") + user.username +
                _("\nMot de passe : **** (celui que vous avez choisi lors de l'inscription)") +
                _("\n\n En étant membre de l'association ResEl vous pouvez profiter de ses nombreux services et des "
                  "activités que l'association propose."),
                from_email=SERVER_EMAIL,
                reply_to=["support@resel.fr"],
                to=[user.email],
            )

            campus_email.send()
            user_email.send()

            self.request.session['logup_ldap_user'] = None
            return render(self.request, self.finalize_template, {'username': user.uid})
        return render(request, self.cgu_template, {'form': form})


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
