from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# Create your views here.
class Reactivation(TemplateView):
    template_name = 'gestion_machines/reactivation.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Reactivation, self).dispatch(*args, **kwargs)

	def get(self, request, *args, **kwargs):
        ldap.reactivation(request.META['REMOTE_ADDR'])
        return render(request, self.template_name)

class Ajout(TemplateView):
	pass

class ChangementCampus(TemplateView):
	template_name = 'gestion_machines/changement-campus.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChangementCampus, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        ldap.update_campus(request.META['REMOTE_ADDR'])
        return render(request, self.template_name)