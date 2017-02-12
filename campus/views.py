from campus.subviews.views_rooms import *
from campus.subviews.views_mails import *


def home_view(request):
    return HttpResponseRedirect(reverse("campus:rooms:calendar"))