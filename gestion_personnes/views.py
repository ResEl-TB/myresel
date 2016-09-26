from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from fonctions import ldap
from fonctions.decorators import resel_required, unknown_machine
from gestion_machines.forms import AddDeviceForm
from gestion_personnes.async_tasks import send_mails
from gestion_personnes.models import LdapUser
from .forms import InscriptionForm, ModPasswdForm, CGUForm, InvalidUID, PersonnalInfoForm


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
            user.inscr_date = datetime.now()
            user.end_cotiz = datetime.now()  # That does not survive the json parser
            user.save()

            # Auto-login the user to simplify his life !
            auth_user = ldap.get_user(username=user.uid)
            if auth_user is not None:
                auth_user.backend = 'django_python3_ldap.auth.LDAPBackend'
                login(request, auth_user)

            send_mails.delay(user)

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

        if form.is_valid():
            user = LdapUser.get(pk=request.user.username)
            user.user_password = form.cleaned_data["password"]
            user.nt_password = form.cleaned_data["password"]
            user.save()

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


class PersonalInfo(View):
    template_name = 'gestion_personnes/personal_info.html'
    form_class = PersonnalInfoForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonalInfo, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial={
            'email': request.ldap_user.mail,
            'phone': request.ldap_user.mobile,
            'campus': request.ldap_user.campus,
            'building': request.ldap_user.building,
            'room': request.ldap_user.room_number,
            'address': request.ldap_user.postal_address
        })
        c = {
            'form': form,
            'user': request.ldap_user,
        }
        return render(request, self.template_name, c)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = request.ldap_user
            # Check if the email is not already in use
            email = form.cleaned_data["email"]
            if email != user.mail and len(LdapUser.filter(mail=email)) > 0:
                form.add_error("email", _("Addresse e-mail déjà utilisée"))
                return render(request, self.template_name, {'form': form})

            address = form.cleaned_data["address"]
            # Generate an address if
            if form.cleaned_data["building"] != "":
                address = LdapUser.generate_address(form.cleaned_data["campus"], form.cleaned_data["building"], form.cleaned_data["room"])

            user.mail = email
            user.mobile = form.cleaned_data["phone"]
            user.campus = form.cleaned_data["campus"]
            user.building = form.cleaned_data["building"]
            user.room_number = form.cleaned_data["room"]
            user.postal_address = address

            messages.success(request, _("Vos informations ont bien été mises à jour."))
            user.save()

            request.session['update'] = True
            redirect_to = request.GET.get('next', '')
            if redirect_to:
                return HttpResponseRedirect(redirect_to)

        return render(request, self.template_name, {'form': form})