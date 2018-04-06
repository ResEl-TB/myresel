from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import Http404
from gestion_personnes.models import LdapGroup, LdapUser
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _


@method_decorator(login_required, name="dispatch")
class ManageCampusModo(View):

    template_name = 'campus/gestion/manage_modo.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.ldap_user.is_staff:
            raise Http404
        return super(ManageCampusModo, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        modos = LdapGroup.get(pk='campusmodo').get_members()
        context = {
            'modos': modos,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class AddCampusModo(View):

    template_name = 'campus/gestion/manage_modo.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.ldap_user.is_staff:
            raise Http404
        return super(AddCampusModo, self).dispatch(request)

    def post(self, request, *args, **kwargs):
        uid = request.POST.get('uid', None)
        if uid:
            try:
                user = LdapUser.get(uid=uid)
                LdapGroup.get(pk='campusmodo').add_member(user.pk)
            except ObjectDoesNotExist:
                messages.error(
                    request,
                    _(uid+" n'est pas un uid valide ou n'existe pas. \
                    Pensez à utiliser l'autocomplétion.")
                )
        return redirect(reverse('campus:gestion:modo'))


@method_decorator(login_required, name="dispatch")
class RemoveCampusModo(View):

    template_name = 'campus/gestion/manage_modo.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.ldap_user.is_staff:
            raise Http404
        return super(RemoveCampusModo, self).dispatch(request)

    def post(self, request, *args, **kwargsé):
        uid = request.POST.get('uid', None)
        if uid:
            LdapGroup.get(pk='campusmodo').remove_member(uid)
        return redirect(reverse('campus:gestion:modo'))
