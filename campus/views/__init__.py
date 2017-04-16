# -*- coding: utf-8 -*-

from campus.views.views_rooms import *
from campus.views.views_mails import *


def home_view(request):
    return HttpResponseRedirect(reverse("campus:who:user-home"))
