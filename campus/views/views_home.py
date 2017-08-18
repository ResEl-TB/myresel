import feedparser

from django.shortcuts import render
from django.views.generic import View
from django.utils import timezone

from django.db.models import Q

from campus.models.rooms_models import RoomBooking
from campus.models.clubs_models import StudentOrganisation
from campus.models.mails_models import Mail

from campus.whoswho.views import ListBirthdays

from myresel.settings import HOME_RSS_LINK

class Home(View):

    template_name = "campus/home.html"

    #@method_decorator(login_required)
    #def dispatch(self, *args, **kwargs):
    #    return super(Home, self).dispatch(self, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        events = RoomBooking.objects.order_by('start_time').filter(
            start_time__gt=timezone.now(),
            displayable=True
        ).all()[:4]
        birthdays = ListBirthdays.get_today_birthdays()
        campus_mails = Mail.objects.order_by('-date').filter(moderated=True).all()[:4]

        python_wiki_rss_url = HOME_RSS_LINK
        feed = feedparser.parse( python_wiki_rss_url )

        context = {
            'events': events,
            'birthdays': birthdays,
            'campus_mails': campus_mails,
            'historicstuff': feed['items'],
        }

        return render(request, self.template_name, context)