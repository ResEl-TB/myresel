from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, mail_admins
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from ldap3 import MODIFY_REPLACE

from fonctions import ldap, generic
from fonctions.decorators import resel_required, unknown_machine
from gestion_machines.forms import AddDeviceForm
from gestion_personnes.models import LdapUser
from .forms import InscriptionForm, ModPasswdForm, CGUForm, InvalidUID


class Inscription(View):
    """
    Vue appelée pour que l'user s'inscrive au ResEl
    C'est cette vue qui créer la fiche LDAP de l'user
    On lui affiche le réglement intérieur, et un formulaire pour remplir les champs LDAP
    """
    # TODO: Choix de la promo
    # TODO: Virer téléphone portable obligatoire

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
            try:
                user = form.to_ldap_user()
            except InvalidUID:
                messages.error(request, _("Une erreur s'est produite lors de la création de vos identifiants. "
                                          "Veuillez contacter un administeur."))
                return render(request, self.template_name, {'form': form})
            request.session['logup_user'] = user.to_json()
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

    def check_session(self):
        """
        Redirect the user if the session is miss configured.
        :return:
        """
        try:
            if not self.request.session['logup_user']:
                return HttpResponseRedirect(reverse('gestion-personnes:inscription'))
        except KeyError:
            return HttpResponseRedirect(reverse('gestion-personnes:inscription'))
        return None

    @method_decorator(resel_required)
    @method_decorator(unknown_machine)
    def dispatch(self, request, *args, **kwargs):
        redirect = self.check_session()
        if redirect:
            return redirect
        return super(InscriptionCGU, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(self.request, self.cgu_template, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = LdapUser.from_json(self.request.session['logup_user'])
            user.save()

            auth_user = ldap.get_user(username=user.uid)
            if auth_user is not None:
                auth_user.backend = 'django_python3_ldap.auth.LDAPBackend'
                login(request, auth_user)

            # Subscribe to campus@resel.fr
            campus_email = EmailMessage(
                subject="SUBSCRIBE campus {} {}".format(user.first_name,
                                                        user.last_name),
                body="Inscription automatique de {} a campus".format(user.uid),
                from_email=user.mail,
                reply_to=["listmaster@resel.fr"],
                to=["sympa@resel.fr"],
            )

            # Send a validation email to the user
            # TODO: rédiger un peu plus ce mail et le faire valider par le respons' com
            # TODO: ajouter un email pour faire valider l'adresse email
            user_email = EmailMessage(
                subject=_("Inscription au ResEl"),
                body="Bonjour," +
                "\nVous êtes désormais inscrit au ResEl, voici vos identifiants :" +
                "\nNom d'utilisateur : " + str(user.uid) +
                "\nMot de passe : **** (celui que vous avez choisi lors de l'inscription)" +

                "\n\n Vous pouvez, si vous souhaitez, changer votre mot de passe (en suivant ce lien https://my.resel.fr/personnes/modification-passwd)" +
                "\n Ainsi que tout les paramètres de votre compte." +

                "\n\n En étant membre de l'association ResEl vous pouvez profiter de ses nombreux services et des "
                  "activités que l'association propose." +
                "\n N'hésitez pas à naviguer sur notre site (https://resel.fr) pour y découvrir tout ce que nous proposons." +

                "\n\nPour avoir accès à internet, vous allez devoir inscrire chacune de vos machines (ordinateurs, smartphones, etc...) à notre réseau." +
                "\nRendez vous sur notre site web, vous serez guidé à travers cette dernière étape." +

                "\n\nSi vous avez le moindre problème, la moindre question, la moindre envie de nous féliciter, ou de nous faire des bisous baveux,"+
                "vous pouvez répondre à cet e-mail, ou venir nous voir pendant nos permanences, celles-ci ont lieu tous les jours en semaine de 18h à 19h30"+
                "au foyer des élèves de Télécom Bretagne."+

                "\n\nSi vous êtes intéressé pour nous aider, pour travailler avec nous au sein de l'association, pour mettre à disposition vos compétences,"+
                "ou même si vous n'avez pas de compétences mais que vous souhaitez apprendre, vous pouvez aussi nous contacter pour faire partie de l'équipe" +
                " d'administrateurs !"+

                "\n\nÀ bientôt, l'équipe ResEl.",
                from_email="inscription@resel.fr",
                to=[user.mail],
            )

            mail_admins("Inscription de %s au ResEl" % str(user.uid),
                        "Nouvel inscrit au ResEl par le site web :"
                        "\n\nuid : %(username)s"
                        "\nNom : %(lastname)s"
                        "\nPrénom : %(firstname)s"
                        "\nemail : %(mail)s"
                        "\nCampus : %(campus)s"
                        "\n\n Ce mail est un mail automatique envoyé par l'interface d'inscription du ResEl. " % {
                            "username": user.uid,
                            "lastname": user.last_name,
                            "firstname": user.first_name,
                            "mail": user.mail,
                            "campus": settings.CURRENT_CAMPUS
                        })

            try:
                campus_email.send()
                user_email.send()
            except Exception:
                pass
                # TODO: show error to user, and notify admin

            self.request.session['logup_user'] = None
            register_form = AddDeviceForm()
            return render(self.request, self.finalize_template, {'username': user.uid, 'register_form': register_form})
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
            dn = 'uid=%s,' % request.user + settings.LDAP_DN_PEOPLE
            modifs = {
                'userpassword': [(MODIFY_REPLACE, [generic.hash_passwd(form.cleaned_data["password"])])],
                'ntpassword': [(MODIFY_REPLACE, [generic.hash_to_ntpass(form.cleaned_data["password"])])],
            }
            ldap.modify(dn, modifs)

            messages.success(request, _("Votre mot de passe a été modifié"))
            return HttpResponseRedirect(reverse('home'))

        return render(request, self.template_name, {'form': form})


class Settings(View):
    template_name = 'gestion_personnes/settings.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Settings, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
