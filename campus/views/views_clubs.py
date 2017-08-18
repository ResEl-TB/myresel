import os
import re
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from smtplib import SMTPException
from django.views.generic import FormView, View

from io import BytesIO
from PIL import Image

from campus.forms import SendMailForm, ClubManagementForm, ClubEditionForm
from campus.models.clubs_models import StudentOrganisation, Association, ListeCampagne
from gestion_personnes.models import LdapUser, LdapGroup
from fonctions.decorators import ae_required

from myresel.settings import MEDIA_ROOT, LDAP_DN_PEOPLE

logger = logging.getLogger("default")

def list_clubs(request):
    """
    The default view, used to list every club, list and assos
    Users can subscribe, prezs can add memebers, edit the club etc.
    """

    organisations = StudentOrganisation.all()

    clubs = [o for o in organisations if "tbClubSport" in o.object_classes or "tbClub" in o.object_classes]
    assos = [o for o in organisations if "tbAsso" in o.object_classes]
    lists = [o for o in organisations if "tbCampagne" in o.object_classes]

    clubs.sort(key=lambda x: x.name)
    assos.sort(key=lambda x: x.name)
    lists.sort(key=lambda x: x.name)

    hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser, hardLinkAddMail = getHardLinks()

    return render(
        request,
        'campus/clubs/list.html',
        {
            'clubs': clubs,
            'assos': assos,
            'lists': lists,
            'ldapOuPeople': LDAP_DN_PEOPLE,
            'hardLinkAdd': hardLinkAdd,
            'hardLinkDel': hardLinkDel,
            'hardLinkAddPrez': hardLinkAddPrez,
            'hardLinkWhoUser': hardLinkWhoUser,
            'hardLinkAddMail': hardLinkAddMail,
        }
    )

class ClubDetail(View):

    template_name = "campus/clubs/detail.html"

    def get(self, request, pk):
        club = StudentOrganisation.get(pk=pk)
        members = club.members
        prez=[]
        if club.prezs:
            prez = club.prezs[0]
            uid = re.search('uid=([a-z0-9]+),', prez).group(1)
            prez = LdapUser.get(pk=uid)
        users = []
        for member in members:
            uid = re.search('uid=([a-z0-9]+),', member).group(1)
            users += [LdapUser.get(pk=uid)]
        return render(request, self.template_name, {"club":club, "members":users, "prez":prez})


@method_decorator(login_required, name="dispatch")
class NewClub(FormView):
    """
    View used to add a new club, list or asso. It shares the same template used
    for club/list/asso edition
    """

    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/campus/clubs'

    def form_valid(self, form):
        if not (self.request.ldap_user.is_campus_moderator() or self.request.user.is_staff):
            messages.error(self.request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        if form.cleaned_data['logo'] != None:
            logo = form.cleaned_data['logo']
            logo = Image.open(BytesIO(logo.read()))
            try:
                path = MEDIA_ROOT+"/image/"+form.cleaned_data['type']+"/"
                os.makedirs(path)
            except FileExistsError:
                pass
            logo.save(path+form.cleaned_data['cn']+".png", "PNG")
            form.cleaned_data['logo'] = form.cleaned_data['cn']+".png"
        form.create_club()
        pk = None
        return super(NewClub, self).form_valid(form)


@method_decorator(login_required, name="dispatch")
class EditClub(FormView):
    """
    View used to edit a club/asso/campagne
    """

    template_name = 'campus/clubs/new_club.html'
    form_class = ClubEditionForm
    success_url = '/campus/clubs'

    def get(self, request, pk):
        try:
            orga = StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")
        if not (request.ldap_user.is_campus_moderator() or request.ldap_user.pk in orga.prezs or request.user.is_staff):
            messages.error(request, _("Vous n'êtes pas modérateur campus ou président(e) de ce club"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))

        if 'tbClub' in orga.object_classes or 'tbClubSport' in orga.object_classes:
            type='CLUB'
        elif 'tbAsso' in orga.object_classes:
            type='ASSOS'
        elif 'tbCampagne' in orga.object_classes:
            type='LIST'

        form = self.form_class(initial={
            'type': type,
            'cn': orga.cn,
            'name': orga.name,
            'description': orga.description,
            'website': orga.website,
            'email': orga.email,
            'campagneYear': orga.campagneYear,
        })
        return render(request, self.template_name, {'form': form, 'pk': pk})

    def form_valid(self, form):
        pk = self.kwargs['pk']
        try:
            orga = StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

        if not (self.request.ldap_user.is_campus_moderator() or self.request.ldap_user.pk in orga.prezs or self.request.user.is_staff):
            messages.error(self.request, _("Vous n'êtes pas modérateur campus ou président(e) de ce club"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))

        if form.cleaned_data['logo'] != None:
            logo = form.cleaned_data['logo']
            logo = Image.open(BytesIO(logo.read()))
            try:
                path = MEDIA_ROOT+"/image/"+form.cleaned_data['type']+"/"
                os.makedirs(path)
            except FileExistsError:
                pass
            logo.save(path+form.cleaned_data['cn']+".png", "PNG")
            form.cleaned_data['logo'] = form.cleaned_data['cn']+".png"

        form.edit_club(pk)

        return super(EditClub, self).form_valid(form)

@method_decorator(login_required, name="dispatch")
class DeleteClub(View):
    """
    View used to remove a club/asso/list
    """

    def post(self, request, pk):
        if not (request.ldap_user.is_campus_moderator() or request.user.is_staff):
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:who:home'))
        try:
            StudentOrganisation.get(cn=pk).delete()
            return redirect('campus:clubs:list')
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

@method_decorator(login_required, name="dispatch")
class MyClubs(View):
    """
    View used to list the current user's clubs
    """

    template_name = 'campus/clubs/list.html'

    def get(self, request):
        orgas = StudentOrganisation.all()
        #legacy feature; because some prezs aren't members in the ldap for some reason
        my_orgas = [c for c in orgas if request.ldap_user.pk in c.members]
        my_orgas += [c for c in orgas if request.ldap_user.pk in c.prezs and c not in my_orgas]
        my_orgas.sort(key=lambda x: x.name)

        clubs = [o for o in my_orgas if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]
        lists = [o for o in my_orgas if "tbCampagne" in o.object_classes]
        assos = [o for o in my_orgas if "tbAsso" in o.object_classes]

        hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser, hardLinkAddMail = getHardLinks()

        context = {
            'clubs': clubs,
            'assos': assos,
            'lists': lists,
            'ldapOuPeople': LDAP_DN_PEOPLE,
            'hardLinkAdd': hardLinkAdd,
            'hardLinkDel': hardLinkDel,
            'hardLinkAddPrez': hardLinkAddPrez,
            'hardLinkWhoUser': hardLinkWhoUser,
        }
        return render(request, self.template_name, context)

class SearchClub(View):
    """
    View used to list clubs matching the user request
    """

    template_name='campus/clubs/list.html'

    def get(self, request):
        what = request.GET.get('what', '').strip()
        organisations = StudentOrganisation.filter(name__contains=what)
        organisations.sort(key=lambda x: x.name)

        clubs = [o for o in organisations if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]
        lists = [o for o in organisations if "tbCampagne" in o.object_classes]
        assos = [o for o in organisations if "tbAsso" in o.object_classes]

        if not (clubs or lists or assos):
            messages.info(request, _("Aucun club ne correspond à votre recherche"))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser, hardLinkAddMail = getHardLinks()

        context = {
            'clubs': clubs,
            'assos': assos,
            'lists': lists,
            'ldapOuPeople': LDAP_DN_PEOPLE,
            'hardLinkAdd': hardLinkAdd,
            'hardLinkDel': hardLinkDel,
            'hardLinkAddPrez': hardLinkAddPrez,
            'hardLinkWhoUser': hardLinkWhoUser,
        }

        return render(request, self.template_name, context)

@method_decorator(login_required, name="dispatch")
class AddPersonToClub(View):
    """
    View used to add a person to a specific club/list or asso if he's got the right to do so
    """

    def add_user(self, user, club, request):
        """
        Add a `user` to a `club` and subscribe him to the mlist, 
        no verification is made.
        """
        club.members.append(user.pk)
        club.save()
        if not club.email:
            return

        mail_search = re.search('^([a-z1-9-_.+]+)\@.+$', club.email)
        mail = mail_search.group(1)
        subscription_email = EmailMessage(
            subject="SUBSCRIBE {} {} {}".format(mail, user.first_name,
                                                    user.last_name),
            body="Inscription automatique de {} à {}".format(user.uid, club.name),
            from_email=user.mail,
            reply_to=["listmaster@resel.fr"],
            to=["sympa@resel.fr"],
        )
        try:
            subscription_email.send()
        except SMTPException:
            logger.warning(
                "Erreur lors de l'inscription à la mlist %s de %s" % (mail, user.mail),
                extra={
                    'uid': user.uid,
                    'user_mail': user.mail,
                    'mlist': mail,
                    'message_code': 'ERROR_SUBSCRIBE',
                    }
                )
        messages.success(request, _("Inscription terminée avec succès"))


    def post(self, request, pk):
        try:
            club = StudentOrganisation.get(cn=pk)
            # If we don't do this we get an error cuz our LDAP scheme does not allow
            # a single model for each type of organisation
            if "tbCampagne" in club.object_classes:
                club = ListeCampagne.get(cn=pk)
            elif "tbAsso" in club.object_classes:
                club = Association.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Le club n'existe pas")

        uid = request.POST.get('id_user', None)
        if uid is None:
            user = request.ldap_user
        else:
            if not (self.request.ldap_user.is_campus_moderator() or self.request.ldap_user.pk in club.prezs or request.user.is_staff):
                messages.error(request, _("Vous n'êtes pas modérateur campus ou président de ce club"))
                return HttpResponseRedirect(reverse('campus:clubs:list'))
            else:
                try:
                    user = LdapUser.get(uid=uid)
                except ObjectDoesNotExist:
                    raise Http404("L'utilisateur n'existe pas")

        if not user.pk in club.members and (("tbClub" in club.object_classes or \
        "tbCampagne" in club.object_classes or "tbClubSport in club.object_classes") or \
        (self.request.ldap_user.is_campus_moderator() or self.request.ldap_user.pk in club.prezs or\
        request.user.is_staff)): # Our ldap is crap
            self.add_user(user, club, request)

        else:
            messages.info(request, _("Le système a déjà trouvé le membre correspondant comme étant inscrit, inscription impossible."))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@method_decorator(login_required, name="dispatch")
class AddMailToClub(View):
    """
    View used to add a person to a specific club/list or asso if he's got the right to do so
    """

    def get(self, request, pk):
        try:
            club=StudentOrganisation.get(cn=pk)
            if "tbCampagne" in club.object_classes:
                club=ListeCampagne.get(cn=pk)
            elif "tbAsso" in club.object_classes:
                club=Association.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

        if not (self.request.ldap_user.is_campus_moderator() or self.request.ldap_user.pk in club.prezs or request.user.is_staff):
            messages.error(request, _("Vous n'êtes pas modérateur campus ou président de ce club"))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        mail = request.GET.get("mail", None)

        if not mail:
            raise Http404
        elif not re.match('^[a-z1-9-_.+]+\@.+$', mail):
            messages.error(request, _("L'email est invalide"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))

        messages.success(request, _("Inscription terminée avec succès"))
        subscription_email = EmailMessage(
            subject="SUBSCRIBE {}".format(club.email),
            body="Inscription par un modérateur campus ou président de club de l'adresse {} à {}".format(mail, club.name),
            from_email=mail,
            reply_to=["listmaster@resel.fr"],
            to=["sympa@resel.fr"],
        )
        try:
            subscription_email.send()
        except SMTPException:
            print("Somthing went wrong when trying to send club subscription message")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@method_decorator(login_required, name="dispatch")
class AddPrezToClub(View):
    """
    View used to add a person to a specific club as a prez
    """

    def post(self, request, pk):

        try:
            club = StudentOrganisation.get(cn=pk)
            #If we don't do this we get an error cuz our LDAP scheme does not allow
            # a single model for each type of organisation
            if "tbCampagne" in club.object_classes:
                club = ListeCampagne.get(cn=pk)
            elif "tbAsso" in club.object_classes:
                club = Association.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

        if not (request.ldap_user.is_campus_moderator() or request.ldap_user.pk in club.prezs or request.user.is_staff):
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        uid = request.POST.get('id_user', None)
        try:
            user = LdapUser.get(uid=uid)
        except ObjectDoesNotExist:
            raise Http404("L'utilisateur n'éxiste pas")

        if "tbClub" in club.object_classes and not user.pk in club.prezs:
            club.prezs = [user.pk]
            club.save()
            messages.success(request, _("Le président viens d'être ajouté"))
        else:
            messages.info(request, _("Cette personne est déjà président(e)"))

        if "tbClub" in club.object_classes and not user.pk in club.members:
            club.members.append(user.pk)
            club.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@method_decorator(login_required, name="dispatch")
class RemovePersonFromClub(View):
    """
    View used to remove a person from a specific club
    """

    def remove_user(self, user, club, request):
        """Remove a `user` from the `club` and sign him off the mlist"""
        club.members.remove(user.pk)
        club.save()
        messages.success(request, _("Désinscription terminée avec succès"))
        if not club.email:
            return
        mail_search = re.search('^([a-z1-9-_.+]+)\@.+$', club.email)
        mail = mail_search.group(1)
        subscription_email = EmailMessage(
            subject="SIGNOFF {} {} {}".format(mail, user.first_name, user.last_name),
            body="Désinscription automatique de {} a {}".format(user.uid, club.name),
            from_email=user.mail,
            reply_to=["listmaster@resel.fr"],
            to=["sympa@resel.fr"],
        )
        try:
            subscription_email.send()
        except SMTPException:
            logger.warning(
                "Erreur lors de la désinscription de la mlist %s de %s" % (mail, user.mail),
                extra={
                    'uid': user.uid,
                    'user_mail': user.mail,
                    'mlist': mail,
                    'message_code': 'ERROR_UNSUBSCRIBE',
                }
            )

    def post(self, request, pk):
        try:
            club = StudentOrganisation.get(cn=pk)
            # If we don't do this we get an error cuz our LDAP scheme does not allow
            # a single model for each type of organisation
            if "tbCampagne" in club.object_classes:
                club = ListeCampagne.get(cn=pk)
            elif "tbAsso" in club.object_classes:
                club = Association.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

        uid = request.POST.get('id_user', None)
        if uid is None:
            user = request.ldap_user
        else:
            try:
                user = LdapUser.get(uid=uid)
            except ObjectDoesNotExist:
                raise Http404("L'utilisateur n'existe pas")
        allowed = (
            self.request.ldap_user.is_campus_moderator()
            or self.request.ldap_user.pk in club.prezs
            or request.user.is_staff
            or user.uid == request.ldap_user
        )

        if allowed and user.pk in club.members:
            self.remove_user(user, club, request)
        else:
            messages.info(request, _("Cette personne ne fait pas partie du club ou alors vous n'êtes pas autorisé"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@method_decorator(login_required, name="dispatch")
class RequestClubs(View):
    """
    View used to request (using ajax) alist of clubs
    """

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            #We check if the request is for memebers or prezs
            what = request.GET.get("term", None)
            if what == None or len(what) <3:
                raise Http404
            clubs = StudentOrganisation.filter(name__contains=what)
            results=[]
            for club in clubs:
                club_json = {}
                club_json['id'] = club.cn
                club_json['label'] = '%s - %s' % (club.name, club.description[:35])
                club_json['value'] = club.cn
                results.append(club_json)
            data = json.dumps(results)
            mimetype = 'application/json'
            return HttpResponse(data, mimetype)
        else:
            raise Http404("")

def getHardLinks():
    """
    Function used to retrieve various hard links
    """

    hardLinkAdd = reverse('campus:clubs:add-person', kwargs={'pk': "a"})[:-1]
    hardLinkDel = reverse('campus:clubs:remove-person', kwargs={'pk': "a"})[:-1]
    hardLinkAddPrez = reverse('campus:clubs:add-prez', kwargs={'pk': "a"})[:-1]
    hardLinkWhoUser = reverse('campus:who:user-details', kwargs={'uid': "a"})[:-1]
    hardLinkAddEmail = reverse('campus:clubs:add-mail', kwargs={'pk': "a"})[:-1]

    return(hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser, hardLinkAddEmail)
