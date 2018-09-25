# -*- coding: utf-8 -*-

from django.views.generic import View
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from gestion_personnes.models import LdapUser
from django.core.exceptions import ObjectDoesNotExist

from gestion_personnes.forms import InscriptionForm

from fonctions import ldap
from datetime import datetime, date

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

    def applySpecialFilter(self, ae_members, type):
        now = date.today()

        i = 0
        while i < len(ae_members):
            end = ae_members[i]['end']
            if checkDate(end):
                end = date(int(end[0:4]), int(end[4:6]), int(end[6:8]))
                if(type == 'former' and end > now):
                    ae_members.pop(i)
                    i-=1
                elif(type == 'current' and end <= now):
                    ae_members.pop(i)
                    i-=1
            i+=1
        return ae_members

    def get(self, request):
        if request.is_ajax():
            filter = request.GET.get('filter', '')
            if not filter:
                users = LdapUser.all()
            else:
                users = []
                for key in self.search_keys:
                    users += LdapUser.filter(**{key+"__contains": filter})
            ae_members = []
            for user in users:
                if(user.n_adherent and user.uid not in [u["uid"] for u in ae_members]):
                    ae_members.append(ldapUserToDict(user))

            # If the user requested an additional filter
            if(request.GET.get('special', 'false') == 'true'):
                # Default to current just in case, uses less data
                type = request.GET.get('search_type', 'current')
                ae_members = self.applySpecialFilter(ae_members, type)

            return JsonResponse({"results": ae_members})
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

def checkDate(date):
    """
    Checks the validity of a date from the dates_member LDAP field
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

class AddUser(View):
    """
    Ajax view adding a new member.
    Very basic verifications, we assume the admin knows what he is doing.
    """

    def post(self, request):
        user = LdapUser()

        start = request.POST.get('start', '').strip()
        end = request.POST.get('end', '').strip()
        if not (checkDate(start) and checkDate(end)):
            return JsonResponse({"error": 2})

        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')

        if(user.first_name == '' or user.last_name == ''):
            return JsonResponse({"error": 3})

        user.uid = InscriptionForm.get_free_uid(user.first_name, user.last_name)
        user.promo = request.POST.get('promo', '')
        user.mail = request.POST.get('email', '')
        user.formation = request.POST.get('training', '')
        user.campus = request.POST.get('campus', '')
        user.n_adherent = request.POST.get('n_adherent', '')

        if(not user.promo or not user.mail or not user.mail or \
           not user.formation or not user.campus or not user.n_adherent):
            return JsonResponse({"error": 3})

        user.mode_paiement = request.POST.get('payment', '')
        user.ae_cotiz = request.POST.get('payment_value', '')
        user.dates_membre = ['-'.join([start,end])]
        user.inscr_date = datetime.now()

        user.save()

        return JsonResponse({"success": True})

class EditUser(View):
    """
    Ajax view editing existing member
    """

    def post(self, request):
        uid = request.POST.get('uid', '')
        try:
            user = LdapUser.get(pk=uid)
        except ObjectDoesNotExist:
            return JsonResponse({"error": 1})

        # The user is a member or is being added
        if(user.n_adherent or request.POST.get('n_adherent', '') != ''):
            start = request.POST.get('start', '').strip()
            end = request.POST.get('end', '').strip()
            if not (checkDate(start) and checkDate(end)):
                return JsonResponse({"error": 2})

            # If new n_adherent => new set of dates
            if(user.n_adherent != request.POST.get('n_adherent', '') and\
               user.n_adherent != ''):
                user.dates_membre.append('-'.join([start,end]))
            else:
                try:
                    user.dates_membre[-1] = '-'.join([start,end])
                except IndexError:
                    user.dates_membre = ['-'.join([start,end])]

            #Update the fields
            user.n_adherent = request.POST.get('n_adherent', '')
            user.mode_paiement = request.POST.get('payment', '')
            user.ae_cotiz = request.POST.get('payment_value', '')
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
