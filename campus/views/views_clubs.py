import os
import re
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.views.generic import FormView, View

from io import BytesIO
from PIL import Image

from campus.forms import SendMailForm, ClubManagementForm, ClubEditionForm
from campus.models.clubs_models import StudentOrganisation
from gestion_personnes.models import LdapUser, LdapGroup
from fonctions.decorators import ae_required

from myresel.settings import MEDIA_ROOT, LDAP_DN_PEOPLE


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

    hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser = getHardLinks()

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
        }
    )

class NewClub(FormView):
    """
    View used to add a new club, list or asso. It shares the same template used
    for club/list/asso edition
    """

    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/campus/clubs'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NewClub, self).dispatch(*args, **kwargs)

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


class EditClub(FormView):
    """
    View used to edit a club/asso/campagne
    """

    template_name = 'campus/clubs/new_club.html'
    form_class = ClubEditionForm
    success_url = '/campus/clubs'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EditClub, self).dispatch(*args, **kwargs)

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

class DeleteClub(View):
    """
    View used to remove a club/asso/list
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DeleteClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        if not (request.ldap_user.is_campus_moderator() or request.user.is_staff):
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:who:home'))
        try:
            StudentOrganisation.get(cn=pk).delete()
            return redirect('campus:clubs:list')
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

class MyClubs(View):
    """
    View used to list the current user's clubs
    """

    template_name = 'campus/clubs/list_clubs.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MyClubs, self).dispatch(*args, **kwargs)

    def get(self, request):
        clubs = StudentOrganisation.all()
        clubs = [o for o in clubs if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]
        #legacy feature; because some prezs aren't members in the ldap for some reason
        myclubs = [c for c in clubs if request.ldap_user.pk in c.members]
        myclubs += [c for c in clubs if request.ldap_user.pk in c.prezs and c not in myclubs]
        myclubs.sort(key=lambda x: x.name)

        hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser = getHardLinks()

        context = {
            'clubs': myclubs,
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

    template_name='campus/clubs/list_clubs.html'

    def get(self, request):
        what = request.GET.get('what', '').strip()
        print(what)
        organisations = StudentOrganisation.filter(name__contains=what)
        clubs = [o for o in organisations if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]
        clubs.sort(key=lambda x: x.name)

        if not clubs:
            messages.info(request, _("Aucun club ne correspond à votre recherche"))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser = getHardLinks()

        context = {
            'clubs': clubs,
            'ldapOuPeople': LDAP_DN_PEOPLE,
            'hardLinkAdd': hardLinkAdd,
            'hardLinkDel': hardLinkDel,
            'hardLinkAddPrez': hardLinkAddPrez,
            'hardLinkWhoUser': hardLinkWhoUser,
        }

        return render(request, self.template_name, context)

class AddPersonToClub(View):
    """
    View used to add a person to a specific club
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddPersonToClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        uid=request.GET.get('id_user', None)
        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

        if uid == None:
            user = request.ldap_user
        else:
            if not (self.request.ldap_user.is_campus_moderator() or self.request.ldap_user.pk in club.prezs or request.user.is_staff):
                messages.error(request, _("Vous n'êtes pas modérateur campus ou président de ce club"))
                return HttpResponseRedirect(reverse('campus:clubs:list'))
            else:
                try:
                    user = LdapUser.get(uid=uid)
                except ObjectDoesNotExist:
                    raise Http404("L'utilisateur n'éxiste pas")

        if "tbClub" in club.object_classes and not user.pk in club.members:
            messages.success(request, _("Inscription terminée avec succès"))
            club.members.append(user.pk)
            club.save()
            if club.email:
                mail_search = re.search('^([a-z1-9-_.+]+)\@.+$', club.email)
                mail = mail_search.group(1)
                subscription_email = EmailMessage(
                    subject="SUBSCRIBE {} {} {}".format(mail, user.first_name,
                                                            user.last_name),
                    body="Inscription automatique de {} a {}".format(user.uid, club.name),
                    from_email=user.mail,
                    reply_to=["listmaster@resel.fr"],
                    to=["sympa@resel.fr"],
                )
                subscription_email.send()
        else:
            messages.info(request, _("Le système a déjà trouvé le membre correspondant comme étant inscrit, inscription impossible."))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class AddPrezToClub(View):
    """
    View used to add a person to a specific club as a prez
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddPrezToClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        uid=request.GET.get('id_user', None)

        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")

        if not (request.ldap_user.is_campus_moderator() or request.ldap_user.pk in club.prezs or request.user.is_staff):
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        try:
            user = LdapUser.get(uid=uid)
        except ObjectDoesNotExist:
            raise Http404("L'utilisateur n'éxiste pas")

        if "tbClub" in club.object_classes and not user.pk in club.prezs:
            club.prezs.append(user.pk)
            club.save()
            messages.success(request, _("Le président viens d'être ajouté"))
        if "tbClub" in club.object_classes and not user.pk in club.members:
            club.members.append(user.pk)
            club.save()
        else:
            messages.info(request, _("Cette personne est déjà président(e)"))

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class RemovePersonFromClub(View):
    """
    View used to remove a person from a specific club
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemovePersonFromClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        uid=request.GET.get('id_user', None)
        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404("Aucun club trouvé")
        if uid == None:
            user = request.ldap_user
        else:
            if not (self.request.ldap_user.is_campus_moderator() or self.request.ldap_user.pk in club.prezs or request.user.is_staff):
                messages.error(request, _("Vous n'êtes pas modérateur campus ou président de ce club"))
                return HttpResponseRedirect(reverse('campus:clubs:list'))
            else:
                try:
                    user = LdapUser.get(uid=uid)
                except ObjectDoesNotExist:
                    raise Http404("L'utilisateur n'éxiste pas")
        if "tbAsso" not in club.object_classes and user.pk in club.members:
            club.members.remove(user.pk)
            club.save()
            if club.email:
                mail_search = re.search('^([a-z1-9-_.+]+)\@.+$', club.email)
                mail = mail_search.group(1)
                subscription_email = EmailMessage(
                    subject="SIGNOFF {} {} {}".format(mail, user.first_name,
                                                            user.last_name),
                    body="Inscription automatique de {} a {}".format(user.uid, club.name),
                    from_email=user.mail,
                    reply_to=["listmaster@resel.fr"],
                    to=["sympa@resel.fr"],
                )
                subscription_email.send()
            messages.success(request, _("Désinscription terminée avec succès"))
        else:
            messages.info(request, _("Le système n'a pas trouvé de personne à désinscrire dans la liste des membres"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class RequestMembers(View):
    """
    View used to request (using ajax) the list of users from a club
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RequestMembers, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            pk = request.GET.get('pk', None)
            if pk == None:
                raise Http404("")
            try:
                club=StudentOrganisation.get(cn=pk)
            except ObjectDoesNotExist:
                raise Http404("")

            #We check if the request is for memebers or prezs
            if request.path == reverse("campus:clubs:request_members"):
                entries = club.members
            elif request.path == reverse("campus:clubs:request_prezs"):
                entries = club.prezs
            else:
                raise Http404("") #U never know
            results = []
            for entry in entries:
                uid = re.search('uid=([a-z0-9]+),', entry).group(1)
                user = LdapUser.get(pk=uid)
                user_json = {}
                user_json['uid'] = user.uid
                user_json['full_name'] = '%(first_name)s %(last_name)s' % {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
                results.append(user_json)
            data = json.dumps(results)
            mimetype = 'application/json'
            return HttpResponse(data, mimetype)
        else:
            raise Http404("")

def getHardLinks():
    """
    View used to retrieve various hard links
    """

    hardLinkAdd = reverse('campus:clubs:add-person', kwargs={'pk': "a"})[:-1]
    hardLinkDel = reverse('campus:clubs:remove-person', kwargs={'pk': "a"})[:-1]
    hardLinkAddPrez = reverse('campus:clubs:add-prez', kwargs={'pk': "a"})[:-1]
    hardLinkWhoUser = reverse('campus:who:user-details', kwargs={'uid': "a"})[:-1]

    return(hardLinkAdd, hardLinkDel, hardLinkAddPrez, hardLinkWhoUser)
