import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.views.generic import FormView, View

from io import BytesIO
from PIL import Image

from campus.forms import SendMailForm, ClubManagementForm
from campus.models.clubs_models import StudentOrganisation
from gestion_personnes.models import LdapUser
from fonctions.decorators import ae_required

from myresel.settings import MEDIA_ROOT


def list_clubs(request):

    organisations = StudentOrganisation.all()

    clubs = [o for o in organisations if "tbClubSport" in o.object_classes or "tbClub" in o.object_classes]
    assos = [o for o in organisations if "tbAsso" in o.object_classes]
    lists = [o for o in organisations if "tbCampagne" in o.object_classes]

    return render(
        request,
        'campus/clubs/list.html',
        {
            'clubs': clubs,
            'assos': assos,
            'lists': lists,
        }
    )

# TODO : gestion des droits
class NewClub(FormView):
    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/campus/clubs'

    def form_valid(self, form):
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
        return super(NewClub, self).form_valid(form)


# TODO : gestion des droits
class EditClub(FormView):
    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/thanks/'

    def get(self, request, pk):
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
            'name': orga.name,
            'cn': orga.cn,
            'description': orga.description,
            'website': orga.website,
            'email': orga.email,
            'campagneYear': orga.campagneYear,
        })
        return render(request, self.template_name, {'form': form, 'pk': pk})

    def form_valid(self, form):
        form.edit_club()
        return super(EditClub, self).form_valid(form)

class DeleteClub(View):
    def get(self, request, pk):
        try:
            StudentOrganisation.get(cn=pk).delete()
            return redirect('campus:clubs:list')
        except ObjectDoesNotExist:
            raise Http404

class SearchClub(View):

    template_name='campus/clubs/search_club.html'

    def get(self, request):
        what = request.GET.get('what', '').strip()
        organisations = StudentOrganisation.filter(name__contains=what)
        clubs = [o for o in organisations if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]
        context={'clubs': clubs}
        return render(request, self.template_name, context)

class AddPersonToClub(View):

    def get(self, request, pk, user=None):

        try:
            club=StudentOrganisation.get(cn=pk)
        except ObjectDoesNotExist:
            raise Http404
        if user == None:
            user = request.ldap_user
        else:
            if not request.ldap_user.is_campus_moderator():
                messages.error(request, _("Vous n'êtes pas modérateur campus"))
                return HttpResponseRedirect(reverse('campus:clubs:list'))
            else:
                try:
                    LdapUser.get("user")
                except ObjectDoesNotExist:
                    raise Http404
        if "tbAsso" not in club.object_classes and user.pk not in club.members:
            club.members.append(user.pk)
            print(club.object_classes)
            club.save()
        return redirect('campus:clubs:list')
