import os
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

    organisations = StudentOrganisation.all()

    clubs = [o for o in organisations if "tbClubSport" in o.object_classes or "tbClub" in o.object_classes]
    assos = [o for o in organisations if "tbAsso" in o.object_classes]
    lists = [o for o in organisations if "tbCampagne" in o.object_classes]

    hardLinkAdd = reverse('campus:clubs:add-person', kwargs={'pk': "a"})[:-1]
    hardLinkDel = reverse('campus:clubs:remove-person', kwargs={'pk': "a"})[:-1]
    hardLinkAddPrez = reverse('campus:clubs:add-prez', kwargs={'pk': "a"})[:-1]

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
        }
    )

# TODO : gestion des droits des prezs
class NewClub(FormView):

    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/campus/clubs'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NewClub, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        if not self.request.ldap_user.is_campus_moderator():
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        if form.cleaned_data['type'] != "CLUB":
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

    template_name = 'campus/clubs/new_club.html'
    form_class = ClubEditionForm
    success_url = '/campus/clubs'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EditClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        if not request.ldap_user.is_campus_moderator():
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        try:
            orga = StudentOrganisation.filter(cn=pk)[0]
        except IndexError:
            raise Http404
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
        if not self.request.ldap_user.is_campus_moderator():
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        if form.cleaned_data['type'] != "CLUB" and form.cleaned_data['logo'] != None:
            logo = Image.open(BytesIO(logo.read()))
            try:
                path = MEDIA_ROOT+"/image/"+form.cleaned_data['type']+"/"
                os.makedirs(path)
            except FileExistsError:
                pass
            logo.save(path+form.cleaned_data['cn']+".png", "PNG")
        form.edit_club(pk)
        return super(EditClub, self).form_valid(form)

class DeleteClub(View):

    def get(self, request, pk):
        if not request.ldap_user.is_campus_moderator():
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        try:
            StudentOrganisation.get(cn=pk).delete()
            return redirect('campus:clubs:list')
        except ObjectDoesNotExist:
            raise Http404

class MyClubs(View):

    template_name = 'campus/clubs/list_clubs.html'

    def get(self, request):
        clubs = StudentOrganisation.all()
        clubs = [c for c in clubs if request.ldap_user.pk in c.members]

        hardLinkAdd = reverse('campus:clubs:add-person', kwargs={'pk': "a"})[:-1]
        hardLinkDel = reverse('campus:clubs:remove-person', kwargs={'pk': "a"})[:-1]
        hardLinkAddPrez = reverse('campus:clubs:add-prez', kwargs={'pk': "a"})[:-1]

        context = {
            'clubs': clubs,
            'ldapOuPeople': LDAP_DN_PEOPLE,
            'hardLinkAdd': hardLinkAdd,
            'hardLinkDel': hardLinkDel,
            'hardLinkAddPrez': hardLinkAddPrez,
        }
        return render(request, self.template_name, context)

class SearchClub(View):

    template_name='campus/clubs/list_clubs.html'

    def get(self, request):
        what = request.GET.get('what', '').strip()
        organisations = StudentOrganisation.filter(name__contains=what)
        clubs = [o for o in organisations if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]

        hardLinkAdd = reverse('campus:clubs:add-person', kwargs={'pk': "a"})[:-1]
        hardLinkDel = reverse('campus:clubs:remove-person', kwargs={'pk': "a"})[:-1]
        hardLinkAddPrez = reverse('campus:clubs:add-prez', kwargs={'pk': "a"})[:-1]

        context = {
            'clubs': clubs,
            'ldapOuPeople': LDAP_DN_PEOPLE,
            'hardLinkAdd': hardLinkAdd,
            'hardLinkDel': hardLinkDel,
            'hardLinkAddPrez': hardLinkAddPrez,
        }

        return render(request, self.template_name, context)

class AddPersonToClub(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddPersonToClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        uid=request.GET.get('id_user', None)
        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404
        if uid == None:
            user = request.ldap_user
        else:
            if not request.ldap_user.is_campus_moderator():
                messages.error(request, _("Vous n'êtes pas modérateur campus"))
                return HttpResponseRedirect(reverse('campus:clubs:list'))
            else:
                try:
                    user = LdapUser.get(uid=uid)
                except ObjectDoesNotExist:
                    raise Http404
        if "tbClub" in club.object_classes and not user.pk in club.members:
            messages.success(request, _("Le membre viens d'être ajouté"))
            club.members.append(user.pk)
            club.save()
        else:
            messages.info(request, _("Cette personne est déjà inscrite"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class AddPrezToClub(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddPersonToClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        if not request.ldap_user.is_campus_moderator():
            messages.error(request, _("Vous n'êtes pas modérateur campus"))
            return HttpResponseRedirect(reverse('campus:clubs:list'))
        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404
        try:
            user = LdapUser.get(uid=uid)
        except ObjectDoesNotExist:
            raise Http404
        if "tbClub" in club.object_classes and not user.pk in club.prezs:
            messages.success(request, _("Le président viens d'être ajouté"))
            club.prezs.append(user.pk)
            club.save()
        else:
            messages.info(request, _("Cette personne est déjà président(e)"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class RemovePersonFromClub(View):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemovePersonFromClub, self).dispatch(*args, **kwargs)

    def get(self, request, pk):
        uid=request.GET.get('id_user', None)
        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404
        if uid == None:
            user = request.ldap_user
        else:
            if not request.ldap_user.is_campus_moderator():
                messages.error(request, _("Vous n'êtes pas modérateur campus"))
                return HttpResponseRedirect(reverse('campus:clubs:list'))
            else:
                try:
                    user = LdapUser.get(uid=uid)
                except ObjectDoesNotExist:
                    raise Http404
        if "tbAsso" not in club.object_classes and user.pk in club.members:
            club.members.remove(user.pk)
            club.save()
            messages.success(request, _("Le membre viens d'être supprimé"))
        else:
            messages.info(request, _("Cette personne ne fait pas partie de ce club"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
