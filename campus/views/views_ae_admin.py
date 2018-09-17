# -*- coding: utf-8 -*-

from django.views.generic import View
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from gestion_personnes.models import LdapUser
from fonctions import ldap

#TODO: AUTH + TESTS !!!!!

class AdminHome(View):

    template_name = 'campus/ae-admin/home.html'

    def get(self, request):
        return render(request, self.template_name, {})

# WIP
class GetUsers(View):
    """
    Ajax view searching for users in the school LDAP.
    It also matches corresponding users in our LDAP
    """

    def get(self, request):
        if request.is_ajax():
            res = ldap.search_ecole(
                """(|
                    (uid=*{0}*)
                    (gidnumber={0})
                    (gecos=*{0}*)
                    (mail=*{0}*)
                    (registeredaddress=*{0}*)
                    (uidnumber={0})
                )""".format("TODO")
            )
            print(res)
            return JsonResponse({"test": "test"})
        else:
            raise Http404("Not found")

class GetMembers(View):
    """
    Ajax view searching for and returning a list of AE members.
    """
    search_keys = ['first_name', 'last_name', 'mail', 'promo']

    def get(self, request):
        if request.is_ajax():
            filter = request.GET.get('filter', '')
            if filter:
                users = []
                for key in self.search_keys:
                    users += LdapUser.filter(**{key+"__contains": filter})
                ae_members = []
                for user in users:
                    if(user.n_adherent and user.uid not in [u["uid"] for u in ae_members]):
                        dates = user.dates_membre[-1].split('-')
                        ae_members.append({
                            "uid": user.uid,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "n_adherent": user.n_adherent,
                            "start": dates[0],
                            "end": dates[1],
                        })
                return JsonResponse({"results": ae_members})
            else:
                return JsonResponse(
                    {"error": _("La recherche ne peux pas être vide")},
                )
        else:
            raise Http404("Not found")
