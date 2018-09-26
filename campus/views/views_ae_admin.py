# -*- coding: utf-8 -*-

from django.views.generic import View, TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from gestion_personnes.models import LdapUser
from django.core.exceptions import ObjectDoesNotExist

from gestion_personnes.forms import InscriptionForm
from fonctions.decorators import ae_admin_required

from fonctions import ldap
from ldapback.backends.ldap.base import Ldap
from datetime import datetime, date

import re

# Error codes for the frontend
USER_NOT_FOUND = 1
INVALID_DATES = 2
MISSING_FIELD = 3

@method_decorator(ae_admin_required, name="dispatch")
class AdminHome(TemplateView):

    template_name = 'campus/ae-admin/home.html'


def ae_user_to_dict(user):
    ae_dates = ['', '']
    if user.dates_membre:
        ae_dates = user.dates_membre[-1].split('-')

    return({
        "uid": user.uid,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "training": user.formation,
        "campus": user.campus,
        "payment": user.mode_paiement,
        "payment_value": user.ae_cotiz,
        "n_adherent": user.n_adherent,
        "start": ae_dates[0],
        "end": ae_dates[1],
    })

@method_decorator(ae_admin_required, name="dispatch")
class GetUsers(View):
    """
    Ajax view searching for users in the school LDAP.
    It also matches corresponding users in our LDAP
    """

    search_keys = ['first_name', 'last_name', 'mail', 'promo', 'uid']

    def get(self, request):
        search_filter = request.GET.get('filter', '')
        which_ldap = request.GET.get('ldap', 'resel')
        if request.is_ajax() and search_filter != '':
            if which_ldap == 'school':
                res = ldap.search_ecole(
                    """(|
                        (uid=*{0}*)
                        (gidnumber={0})
                        (gecos=*{0}*)
                        (mail=*{0}*)
                        (registeredaddress=*{0}*)
                        (uidnumber={0})
                    )""".format(Ldap.sanitize(search_filter))
                )
                if not res:
                    res = []
            else:
                res = []
                uids = []
                for key in self.search_keys:
                    users = LdapUser.filter(**{key+"__contains": search_filter})
                    for user in users:
                        if user.uid not in uids:
                            uids.append(user.uid)
                            res.append(ae_user_to_dict(user))
            return JsonResponse({
                "results": res, "from_school_ldap": which_ldap == 'school'
            })
        else:
            raise Http404("Not found")

@method_decorator(ae_admin_required, name="dispatch")
class GetMembers(View):
    """
    Ajax view searching for and returning a list of AE members.
    """
    search_keys = ['first_name', 'last_name', 'mail', 'promo']

    def applySpecialFilter(self, ae_members, filter_type):
        now = date.today()

        i = 0
        while i < len(ae_members):
            end = ae_members[i]['end']
            if checkDate(end):
                end = date(int(end[0:4]), int(end[4:6]), int(end[6:8]))
                if(filter_type == 'former' and end > now):
                    ae_members.pop(i)
                elif(filter_type == 'current' and end <= now):
                    ae_members.pop(i)
                else:
                    i+=1
            else:
                i+=1
        return ae_members

    def get(self, request):
        if request.is_ajax():
            search_filter = request.GET.get('filter', '')
            if not search_filter:
                #TODO: Improve this line for filtered requests
                users = LdapUser.all()
            else:
                users = []
                for key in self.search_keys:
                    users += LdapUser.filter(**{key+"__contains": search_filter})
            ae_members = []
            for user in users:
                if(user.n_adherent and user.uid not in [u["uid"] for u in ae_members]):
                    ae_members.append(ae_user_to_dict(user))

            # If the user requested an additional filter
            if(request.GET.get('special', 'false') == 'true'):
                # Default to current just in case, uses less data
                filter_type = request.GET.get('search_type', 'current')
                ae_members = self.applySpecialFilter(ae_members, filter_type)

            return JsonResponse({"results": ae_members})
        else:
            raise Http404("Not found")

@method_decorator(ae_admin_required, name="dispatch")
class GetAdmins(View):

    def get(self, request):
        if request.is_ajax():
            ae_admins = LdapUser.filter(**{"ae_admin": "TRUE"})
            admins = []
            for admin in ae_admins:
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

@method_decorator(ae_admin_required, name="dispatch")
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
            return JsonResponse({"error": INVALID_DATES})

        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')

        if(user.first_name == '' or user.last_name == ''):
            return JsonResponse({"error": MISSING_FIELD})

        user.uid = InscriptionForm.get_free_uid(user.first_name, user.last_name)
        user.promo = request.POST.get('promo', '')
        user.mail = request.POST.get('email', '')
        user.formation = request.POST.get('training', '')
        user.campus = request.POST.get('campus', '')
        user.n_adherent = request.POST.get('n_adherent', '')

        if(not user.promo or not user.mail or not user.mail or \
           not user.formation or not user.campus or not user.n_adherent):
            return JsonResponse({"error": MISSING_FIELD})

        user.mode_paiement = request.POST.get('payment', '')
        user.ae_cotiz = request.POST.get('payment_value', '')
        user.dates_membre = ['-'.join([start,end])]
        user.inscr_date = datetime.now()

        user.save()

        return JsonResponse({"success": True})

@method_decorator(ae_admin_required, name="dispatch")
class EditUser(View):
    """
    Ajax view editing existing member
    """

    def post(self, request):
        uid = request.POST.get('uid', '')
        try:
            user = LdapUser.get(pk=uid)
        except ObjectDoesNotExist:
            return JsonResponse({"error": USER_NOT_FOUND})

        # The user is a member or is being added
        if(user.n_adherent or request.POST.get('n_adherent', '') != ''):
            start = request.POST.get('start', '').strip()
            end = request.POST.get('end', '').strip()
            if not (checkDate(start) and checkDate(end)):
                return JsonResponse({"error": INVALID_DATES})

            ae_dates = '-'.join([start,end])

            # Avoids an issue with the ldap:
            # You can't have the same set of dates twice
            if ae_dates in user.dates_membre:
                date_index = user.dates_membre.index(ae_dates)
                user.dates_membre.pop(date_index)

            # If new n_adherent => new set of dates
            if(user.n_adherent != request.POST.get('n_adherent', '') and\
               user.n_adherent != ''):
                user.dates_membre.append(ae_dates)
            else:
                try:
                    user.dates_membre[-1] = ae_dates

                except IndexError:
                    user.dates_membre = [ae_dates]

            #Update the fields
            user.n_adherent = request.POST.get('n_adherent', '')
            user.mode_paiement = request.POST.get('payment', '')
            user.ae_cotiz = request.POST.get('payment_value', '')
            user.save()
        else:
            return JsonResponse({"error": USER_NOT_FOUND})

        return JsonResponse({"success": True})

@method_decorator(ae_admin_required, name="dispatch")
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

@method_decorator(ae_admin_required, name="dispatch")
class DeleteAdmin(View):
    """
    Ajax view to remove an admin
    """
    # TODO: Maybe switch to delete method ?
    def post(self, request):
        if request.is_ajax():
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
        else:
            raise Http404
