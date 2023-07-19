from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import View
from django.utils import timezone
from django.utils.decorators import method_decorator

from campus.models.rooms_models import RoomBooking
from campus.models.mails_models import Mail

from campus.whoswho.views import ListBirthdays

@method_decorator(login_required, name="dispatch")
class Home(View):

    template_name = "campus/home.html"

    def get(self, request, *args, **kwargs):
        events = RoomBooking.objects.order_by('start_time').filter(
            start_time__gt=timezone.now(),
            displayable=True
        ).all()[:4]
        birthdays = ListBirthdays.get_today_birthdays()
        campus_mails = Mail.objects.order_by('-date').filter(moderated=True).all()[:4]

        context = {
            'events': events,
            'birthdays': birthdays,
            'campus_mails': campus_mails,
        }

        return render(request, self.template_name, context)
