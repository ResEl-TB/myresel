from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.views.generic import FormView

from campus.forms import SendMailForm, ClubManagementForm
from campus.submodels.clubs_models import StudentOrganisation


def list_clubs(request):
    organisations = StudentOrganisation.all()

    clubs = [o for o in organisations if o.object_classes == "tbClub"]
    assos = [o for o in organisations if o.object_classes == "tbAsso"]

    return render(
        request,
        'campus/clubs/list.html',
        {
            'clubs': clubs,
            'assos': assos,
        }
    )

class NewClub(FormView):
    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/thanks/'

    def form_valid(self, form):
        form.create_club()
        return super(NewClub, self).form_valid(form)


# TODO : gestion des droits
class EditClub(FormView):
    template_name = 'campus/clubs/new_club.html'
    form_class = ClubManagementForm
    success_url = '/thanks/'

    def form_valid(self, form):
        form.edit_club()
        return super(EditClub, self).form_valid(form)