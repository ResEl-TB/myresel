# -*- coding: utf-8 -*-

from django.views.generic import View
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from gestion_personnes.models import LdapUser
from django.core.exceptions import ObjectDoesNotExist

from fonctions import ldap

import re

#TODO: AUTH + TESTS !!!!!

class AdminHome(View):

    template_name = 'campus/ae-admin/home.html'

    def get(self, request):
        return render(request, self.template_name, {})

# WIP

def ldapUserToDict(user):
    if user.dates_membre:
        dates = user.dates_membre[-1].split('-')
    else:
        dates = ['','']
    return({
        "uid": user.uid,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "training": user.formation,
        "campus": user.campus,
        "payment": user.mode_paiement,
        "payment_value": user.ae_cotiz,
        "n_adherent": user.n_adherent,
        "start": dates[0],
        "end": dates[1],
    })

class GetUsers(View):
    """
    Ajax view searching for users in the school LDAP.
    It also matches corresponding users in our LDAP
    """

    search_keys = ['first_name', 'last_name', 'mail', 'promo', 'uid']

    def get(self, request):
        filter = request.GET.get('filter', '')
        which_ldap = request.GET.get('ldap', 'resel')
        print(filter, which_ldap)
        if request.is_ajax() and filter != '':
            if which_ldap == 'school':
                res = ldap.search_ecole(
                    """(|
                        (uid=*{0}*)
                        (gidnumber={0})
                        (gecos=*{0}*)
                        (mail=*{0}*)
                        (registeredaddress=*{0}*)
                        (uidnumber={0})
                    )""".format(filter)
                )
                if not res:
                    res = []
            else:
                res = []
                uids = []
                for key in self.search_keys:
                    users = LdapUser.filter(**{key+"__contains": filter})
                    for user in users:
                        if user.uid not in uids:
                            uids.append(user.uid)
                            res.append(ldapUserToDict(user))
            return JsonResponse({
                "results": res, "from_school_ldap": which_ldap == 'school'
            })
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
                        ae_members.append(ldapUserToDict(user))
                return JsonResponse({"results": ae_members})
            else:
                return JsonResponse(
                    {"error": _("La recherche ne peux pas être vide")},
                )
        else:
            raise Http404("Not found")

class GetAdmins(View):

    def get(self, request):
        if request.is_ajax():
            aeAdmins = LdapUser.filter(**{"ae_admin": "TRUE"})
            admins = []
            for admin in aeAdmins:
                admins.append({
                    'uid': admin.uid,
                    'first_name': admin.first_name,
                    'last_name': admin.last_name
                })
            return JsonResponse({'results': admins})
        else:
            raise Http404("Not found")

class EditFromCSV(View):
    """
    Ajax view editing existing member after dumping a csv file from the client
    """

    def checkDate(self, date):
        """
        Checks the validity of a dates
        """
        try:
            y,m,d = [int(date[0:4]),int(date[4:6]),int(date[6:8])]
            if(1970<y and 0<m<13 and 0<d<32 and len(date) == 8):
                is_okay = True
            else:
                is_okay = False
        except Exception:
            is_okay = False
        return is_okay

    def post(self, request):
        uid = request.POST.get('uid', '')
        try:
            user = LdapUser.get(pk=uid)
        except ObjectDoesNotExist:
            return JsonResponse({"error": 1})

        if(user.n_adherent):
            start = request.POST.get('start', '').strip()
            end = request.POST.get('end', '').strip()
            if not (self.checkDate(start) and self.checkDate(end)):
                return JsonResponse({"error": 2})

            user.dates_membre[-1] = '-'.join([start,end])
            user.save()
        else:
            return JsonResponse({"error": 1})

        return JsonResponse({"success": True})

class AddAdmin(View):
    """
    Ajax view to add a new admin
    """
    def post(self, request):
        uid = request.POST.get('uid', '')

        try:
            user = LdapUser.get(pk=uid)
        except ObjectDoesNotExist:
            return JsonResponse({"error": _('Utilisateur introuvable')})

        if(user.ae_admin):
            return JsonResponse({"error": _('Cet utilisateur est déjà admin')})
        else:
            user.ae_admin = True
            user.save()

        return JsonResponse({'success': 'true'})

class DeleteAdmin(View):
    """
    Ajax view to remove an admin
    """
    def post(self, request):
        uid = request.POST.get('uid', '')

        try:
            user = LdapUser.get(pk=uid)
        except ObjectDoesNotExist:
            return JsonResponse({"error": _('Utilisateur introuvable')})

        if(not user.ae_admin):
            return JsonResponse({"error": _('Cet utilisateur n\'est pas admin')})

        if(user.uid == request.user.username):
            return JsonResponse({"error": _('Vous ne pouvez pas vous supprimer\
            de la liste')})
        else:
            user.ae_admin = False
            user.save()

        return JsonResponse({'success': 'true'})
