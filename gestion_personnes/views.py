from datetime import datetime, timedelta, date
import time
import re

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.mail import EmailMessage

from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, View

from fonctions import ldap
from fonctions.decorators import resel_required, unknown_machine
from gestion_machines.forms import AddDeviceForm
from gestion_personnes.async_tasks import send_mails
from gestion_personnes.models import LdapUser, UserMetaData
from .forms import InscriptionForm, ModPasswdForm, CGUForm, InvalidUID, PersonnalInfoForm, ResetPwdSendForm, \
    ResetPwdForm, SendUidForm, RoutingMailForm
import unicodedata

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

            # Add 7 free days :
            free_duration = timedelta(days=7)  # TODO: move that to config file
            user.end_cotiz = datetime.now() + free_duration  # That does not survive the json parser
            user.save()

            user_meta, __ = UserMetaData.objects.get_or_create(uid=user.uid)
            user_meta.send_email_validation(user.mail, request.build_absolute_uri)

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

            if user.mail != email:
                user_meta, __ = UserMetaData.objects.get_or_create(uid=user.uid)
                user_meta.send_email_validation(email, request.build_absolute_uri)

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


class ResetPwdSend(FormView):
    template_name = 'gestion_personnes/reset_pwd_send.html'
    form_class = ResetPwdSendForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.send_reset_email(self.request)
        messages.info(self.request, _(
            "Nous venons de vous envoyer un e-mail de réinitialisation que vous devriez recevoir d'ici peu."
            " Cliquez sur le lien fournit dans l'e-mail pour continuer la procédure."
        ))
        return super(ResetPwdSend, self).form_valid(form)


class SendUid(FormView):
    """
    View to get send the uid of a user from its email
    """
    template_name = 'gestion_personnes/get_uid_from_email.html'
    form_class = SendUidForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.send_email(self.request)
        messages.info(self.request, _(
            "Nous venons de vous envoyer un e-mail sur votre addresse avec votre identifiant ResEl."
        ))
        return super(SendUid, self).form_valid(form)


class ResetPwd(View):
    """
    View where the user can type a new password
    """
    template_name = 'gestion_personnes/mod-passwd.html'
    form_class = ResetPwdForm
    success_url = reverse_lazy("home")

    def get(self, request, *args, **kwargs):
        key = self.kwargs["key"]
        try:
            UserMetaData.objects.get(reset_pwd_code=key).uid
        except ObjectDoesNotExist:
            return HttpResponseForbidden()
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        key = self.kwargs["key"]
        try:
            uid = UserMetaData.objects.get(reset_pwd_code=key).uid
        except ObjectDoesNotExist:
            return HttpResponseForbidden()

        form = self.form_class(request.POST)
        if form.is_valid():
            form.reset_pwd(uid)
            form.send_reset_email(uid)
            messages.info(request, _(
                "Nous venez de réinitialiser votre mot de passe. " +
                "Vous pouvez désormais vous connecter avec le nouveau mot de passe."
            ))
            return HttpResponseRedirect(self.success_url)
        return render(request, self.template_name, {'form': form})


class CheckEmail(View):
    """
    View where the user can ask for a new email validation/validate his email
    """
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CheckEmail, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        key = self.kwargs.get("key")
        user_info, __ = UserMetaData.objects.get_or_create(uid=request.ldap_user.uid)
        if key is None:
            if user_info.email_validated:
                messages.error(request, _("Votre addresse e-mail a déjà été validée, vous n'avez donc pas besoin de la valider une seconde fois."))
            else:
                user_info.send_email_validation(request.ldap_user.mail, request.build_absolute_uri)
                messages.info(request, _(
                    "Nous venons de vous envoyer un e-mail avec un lien que vous devrez suivre pour valider votre addresse e-mail."))
        else:
            try:
                u = UserMetaData.objects.get(email_validation_code=key)
                u.email_validated = True
                u.save()
                messages.info(request, _("Votre addresse e-mail est bien validée."))
            except ObjectDoesNotExist:
                return HttpResponseForbidden()
        return HttpResponseRedirect(reverse("home"))


class MailResEl(View):
    """
    Base view to present mail configuration parameters, to propose mail
    creation and destruction.
    """
    template_name = 'gestion_personnes/mail_resel.html'

    def build_address(self, uid, first_name, last_name):
        handle = first_name + '.' + last_name
        
        # If he already exist...
        uid_num = re.match("^[a-z._-]+?([0-9].*)$", uid)

        address = handle + str(uid_num.group(1)) + '@resel.fr'
        bearer = LdapUser.filter(object_classes='mailPerson', mail_local_address=address)


        if bearer is None or len(bearer) == 0:
            # SO : http://stackoverflow.com/q/517923
            handle = unicodedata.normalize('NFKD', handle + str(uid_num.group(1))).encode('ASCII',
            'ignore').lower()
        else:
            handle = None

        return handle

    def get(self, request, *args, **kwargs):
        """ 
            Display either :
                - Creation form with rules if has no mail
                - Configuration options and redirection if is a mailPerson
        """

        # Is he already a mailPerson ?
        user = LdapUser.get(pk=request.user.username)
        mail_proposed_address = None

        if 'mailPerson' in user.object_classes and " " not in user.mail_local_address:
            template_name = 'gestion_personnes/mail_resel.html'
            mail_address = user.mail_local_address[0]

            return render(request, template_name, {'user': user, 'user_mail_address': mail_address})

        else:
            template_name = 'gestion_personnes/mail_resel_new.html'
            mail_proposed_address = self.build_address(user.uid, user.first_name, user.last_name)
            mail_proposed_address += b'@resel.fr'

            return render(request, template_name, {'user': user,
            'mail_proposed_address': mail_proposed_address})



    def post(self, request, *args, **kwargs):
        # Turning him into a mail person.
        user = LdapUser.get(pk=request.user.username)
        if 'mailPerson' not in user.object_classes or user.mail_local_address[0] == " ":
            # Get the right left part
            homeDir = '/var/mail/virtual/'+user.uid
            mailDir = user.uid + '/Maildir/'
            
            handle = self.build_address(user.uid, user.first_name, user.last_name)

            if handle:
                mail_address = handle + b'@resel.fr'

                bearer = LdapUser.filter(object_classes='mailPerson', mail_local_address=str(mail_address))

                if len(bearer) != 0:
                    messages.error(request, 
                                    'Impossible de créer une adresse mail unique. Contactez support@resel.fr.')

                    return HttpResponseRedirect(reverse("gestion-personnes:mail"))


                user.mail_local_address = mail_address
                user.mail_dir = mailDir
                user.mail_del_date = None
                user.home_directory = homeDir
                user.object_classes.append('mailPerson')
                user.save()

                # TODO: Send base instructions in first email
                # TODO: Do not hardcode text (i18n)
                # Validate mailbox
                creation_mail = EmailMessage(
                    subject='Création de votre boîte mail ResEl',
                    body='Bonjour, \n' +
                        'Votre nouvelle boîte mail vient d\'être créée.\n' +
                        'Cordialement, \n L\'équipe ResEl',
                    from_email='noreply@resel.fr',
                    reply_to=('support@resel.fr',),
                    to=mail_address)

                creation_mail.send()
                
                messages.success(request, 
                                'Votre boîte mail a été créée avec succès.')

                return HttpResponseRedirect(reverse("gestion-personnes:mail"))
            else:
                messages.error(request,
                    _("Impossible de créer correctement l'adresse. Contactez support@resel.fr"))
                return HttpResponseRedirect(reverse("gestion-personnes:mail"))

        else:
            messages.error(request, 
                    _("Vous avez déjà une adresse ResEl."))
            return HttpResponseRedirect(reverse("gestion-personnes:mail"))

class DeleteMailResEl(View):
    """
        Handles deletion of email address and explications to the user.
    """

    def get(self, request, *args, **kwargs):
        user = LdapUser.get(pk=request.user.username)

        if "mailPerson" not in user.object_classes or " " in user.mail_local_address:
            messages.error(request, _("Cette adresse email n'existe pas ou plus."))
            return HttpResponseRedirect(reverse("gestion-personnes:mail"))

        template_name = "gestion_personnes/delete_mail.html"
        mail_address = user.mail_local_address[0]
        # TODO : check it exists and is linked to this user
        return render(request, template_name, {'user_mail_address': mail_address})

    def post(self, request, *args, **kwargs):
        # Get the user address
        user = LdapUser.get(pk=request.user.username)

        if user.mail_local_address[0] is None:
            messages.error(request, 
                    _("Vous n'avez pas d'adresse."))
            return HttpResponseRedirect(reverse("gestion-personnes:mail"))
        else:
            """ 
                To delete a mail address : 
                - Empty mail_local_address field
                - Add maildeldate attribute
            """
            if request.POST.get('delete_field', None) == user.mail_local_address[0]:
                # TODO: Delete this field !
                user.mail_routing_address = ''
                user.mail_local_address = ' '
                user.mail_del_date = date.fromtimestamp(time.time() + 31 * 24 * 3600)
                user.save()

                messages.success(request, _("Votre demande de suppression a bien été enregistrée."))
                return HttpResponseRedirect(reverse("gestion-personnes:mail"))
            else:
                messages.error(request, _("L'adresse entrée ne correspond pas à votre adresse email."))
                return HttpResponseRedirect(reverse("gestion-personnes:delete-mail"))

class RedirectMailResEl(View):
    template_name = "gestion_personnes/mail_redirect.html"

    def get(self, request, *args, **kwargs):
        user = LdapUser.get(pk=request.user.username)

        if "mailPerson" not in user.object_classes or " " in user.mail_local_address:
                messages.error(request, _("Vous n'avez pas ou plus d'adresse email."))
                return HttpResponseRedirect(reverse("gestion-personnes:mail"))
        else:
            routing_address = user.mail_routing_address
            # TODO: Be sure to select @resel.fr (!)
            # Some still have @resel.enst-bretagne.fr mail adresses (and they should keep it)
            mail_address = user.mail_local_address[0]
            mail_form = RoutingMailForm(initial={'new_routing_address': routing_address})

            return render(request, self.template_name, {"user_mail_address": mail_address, "user_routing_address": routing_address, "mail_form": mail_form})

    def post(self, request, *args, **kwargs):
        user = LdapUser.get(pk=request.user.username)
        if "mailPerson" not in user.object_classes or " " in user.mail_local_address:
                messages.error(request, _("Vous n'avez pas encore d'adresse email."))
                return HttpResponseRedirect(reverse("gestion-personnes:mail"))
        else:
            mail_form = RoutingMailForm(request.POST)
            #new_routing_address = request.POST.get("new_routing_address", None)

            if mail_form.is_valid():
                new_routing_address = mail_form.cleaned_data.get('new_routing_address', None)
            else:
                new_routing_address = None

            if new_routing_address is None:
                return HttpResponseRedirect(reverse("gestion-personnes:redirect-mail"))
            elif new_routing_address == "":
                # User cancelled its redirection
                user.mail_routing_address = ""
                user.save()
                messages.success(request, _("La redirection a bien été supprimée."))
                return HttpResponseRedirect(reverse("gestion-personnes:redirect-mail"))
            else:
                user.mail_routing_address = new_routing_address
                user.save()

                messages.success(request, _("La redirection a bien été créée."))
                return HttpResponseRedirect(reverse("gestion-personnes:redirect-mail"))

