from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage

from campus.forms import SendMailForm
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
