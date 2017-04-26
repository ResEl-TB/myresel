from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.views.generic import FormView

from campus.forms import SendMailForm, ClubManagementForm
from campus.models.clubs_models import StudentOrganisation
from fonctions.decorators import ae_required


def list_clubs(request):

    #TODO: Peupler le LDAP avec des placeholders
    '''
    test = StudentOrganisation()
    test.cn="test"
    test.name="Test"
    test.ml_infos=False
    test.description="Ceci est un test, ce n'est donc pas un vrai club, mais ça vous vous en doutez !"
    test.object_classes="tbClub"
    test.save()
    '''

    organisations = StudentOrganisation.all()

    #TODO: Gérer les clubs dont l'object_classes n'est pas tbClub
    #TODO: Image pour les clubs (?) Et pour les assos

    clubs = [o for o in organisations if "tbClub" in o.object_classes]
    assos = [o for o in organisations if "tbAsso" in o.object_classes]

    return render(
        request,
        'campus/clubs/list.html',
        {
            'clubs': clubs,
            'assos': assos,
        }
    )

# TODO : gestion des droits
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
