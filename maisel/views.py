from datetime import datetime
from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from fonctions.decorators import maisel_manager_required
from fonctions.generic import next_august_fifteenth
from gestion_personnes.models import LdapUser
from .forms import ApproveEmployeeForm


@method_decorator(maisel_manager_required, name='dispatch')
class ManagementView(FormMixin, ListView):
    """View called to show Maisel/MDE employee list"""

    context_object_name = 'employees'
    template_name = 'maisel/list_employees.html'
    form_class = ApproveEmployeeForm

    def get_queryset(self):
        return LdapUser.filter(object_class='maiselEmployee')

    def get(self, request, *args, **kwargs):
        self.form = self.get_form(self.form_class)
        return ListView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        def approve(user):
            user.end_cotiz = next_august_fifteenth()
            user.save()
        self.form = self.get_form(self.form_class)
        if self.form.is_valid():
            action = self.form.cleaned_data['action']
            employee = self.form.cleaned_data['employee']
            if employee == '%all' and action == 'approve':
                for user in LdapUser.filter(object_class='maiselEmployee'):
                    approve(user)
                messages.success(self.request, _("Les agents ont été approuvés."))
            else:
                user = LdapUser.get(pk=employee)
                if action == 'approve':
                    approve(user)
                    messages.success(self.request, _("L’agent a été approuvé."))
                elif action == 'suspend':
                    user.end_cotiz = datetime.now().astimezone()
                    user.save()
                    messages.success(self.request, _("Les accès de l’agent ont été suspendus."))
                else:
                    user.employee_type = ''
                    user.save()
                    messages.success(self.request, _("L’agent a été supprimé."))
        else:
            messages.error(self.request, _("Une erreur est survenue."))
        return self.get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ManagementView, self).get_context_data(*args, **kwargs)
        context['form'] = self.form
        context['august'] = next_august_fifteenth()
        return context
