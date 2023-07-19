import json
import datetime
import os

from io import BytesIO
from PIL import Image

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View

from ldap3.core.exceptions import LDAPException

from gestion_personnes.async_tasks import send_mails
from gestion_personnes.models import LdapUser, UserMetaData

from campus.forms import MajPersonnalInfo, SearchSomeone
from campus.models.clubs_models import StudentOrganisation

from fonctions.generic import today

from myresel.settings import MEDIA_ROOT


class UserDetails(View):
    """
    View used to see and update user's godparents and
    goddaughter/godson
    """

    template_name = 'campus/whoswho/userDetails.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDetails, self).dispatch(*args, **kwargs)

    def get(self, request, uid):
        try:
            user = LdapUser.get(uid=uid)
        except ObjectDoesNotExist:
            raise Http404

        user.godchildren, user.godparents = self.getGods(user)
        clubs = StudentOrganisation.all()
        clubs = [o for o in clubs if "tbClub" in o.object_classes or "tbClubSport" in o.object_classes]
        #legacy feature; because some prezs aren't members in the ldap for some reason
        userClubs = [c for c in clubs if user.pk in c.members]
        userClubs += [c for c in clubs if user.pk in c.prezs and c not in userClubs]
        userClubs.sort(key=lambda x: x.name)
        return render(request, self.template_name, {'display_user' : user, 'clubs':userClubs})

    def getGods(self, user):
        """
        function used to get user's godchildren and godparents
        """

        godparents = []
        godchildren = []
        for line in user.uid_godchildren:
            try:
                godchildren.append(LdapUser.get(uid=line[4:line.find(',')]))
            except ObjectDoesNotExist:
                pass

        for line in user.uid_godparents:
            try:
                godparents.append(LdapUser.get(uid=line[4:line.find(',')]))
            except ObjectDoesNotExist:
                pass

        sorted(godchildren, key=lambda e: e.first_name + " " + e.last_name.upper())
        sorted(godparents, key=lambda e: e.first_name + " " + e.last_name.upper())

        return(godchildren, godparents)


class UserHome(View):
    """
    View used to see and update user's godparents and
    goddaughter/godson and also search for another user/users
    This is the default view for the whoswho
    """

    template_name = 'campus/whoswho/userHome.html'
    form_class = MajPersonnalInfo

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserHome, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):

        user = request.ldap_user

        form = self.form_class(initial={
            'email' : user.mail,
            'campus' : user.campus,
            'building' : user.building,
            'room' : user.room_number,
            'address' : user.postal_address,
            'birth_date' : user.birth_date,
            'is_public' : user.is_public,
        })


        formSearchUser = SearchSomeone()

        user.godchildren, user.godparents = UserDetails.getGods(self, user)

        context = {'user': user, 'form': form, 'formSearchUser': formSearchUser}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        formSearchUser = SearchSomeone()
        user = request.ldap_user

        user.godchildren, user.godparents = UserDetails.getGods(self, user)
        context={'form': form, 'user': user,}

        if form.is_valid():

            mail = form.cleaned_data["email"]

            if mail != user.mail and len(LdapUser.filter(mail=mail)) > 0:
                form.add_error("email", _("Addresse e-mail déjà utilisée"))
                return render(request, self.template_name, context)

            address = form.cleaned_data["address"]

            if form.cleaned_data["campus"] != "None":
                address = LdapUser.generate_address(form.cleaned_data["campus"], form.cleaned_data["building"], form.cleaned_data["room"])

            if user.mail != mail:
                user_meta, __ = UserMetaData.objects.get_or_create(uid=user.uid)
                user_meta.send_email_validation(mail, request.build_absolute_uri)

            #TODO: something better and re-usable
            photo_file = request.FILES.get('photo', False)
            remove_photo = form.cleaned_data["remove_photo"]
            if photo_file: #If the user uploads a photo and at the same time wants to remove it, we assule he just wants a new one
                photo = Image.open(BytesIO(photo_file.read()))
                try:
                    path = MEDIA_ROOT+"/image/users_photo/PROMO_"+user.promo+"/"
                    os.makedirs(path)
                except FileExistsError:
                    pass
                photo.save(path+user.uid, "PNG")
                user.photo_file = "PROMO_"+user.promo+"/"+user.uid
            elif remove_photo:
                user.photo_file = ""

            user.mail = mail
            user.campus = form.cleaned_data["campus"]
            user.building = form.cleaned_data["building"]
            user.room_number = form.cleaned_data["room"]
            user.postal_address = address
            user.birth_date = form.cleaned_data["birth_date"]
            user.is_public = form.cleaned_data["is_public"]
            user.save()

            messages.success(request, _("Vos Informations ont été mises à jour"))
        else:
            messages.warning(request, _("Une ou plusieurs informations sont invalides"))

        context={'user': user, 'form': form, 'formSearchUser': formSearchUser}
        return render(request, self.template_name, context)

@method_decorator(login_required, name="dispatch")
class SearchUsers(View):
    """
    View used to search for users
    """

    template_name = 'campus/whoswho/searchUsers.html'

    def get(self, request, *args, **kwargs):
        form = SearchSomeone(request.GET)
        if form.is_valid():
            res = form.get_results(form.cleaned_data["what"], form.cleaned_data["strict"])
            if res:
                return render(request, self.template_name, {'users': res, 'form': form})
            else:
                messages.info(request, _("La recherche n'a rien retourné"))
        else:
            messages.error(request, _("Le contenu de la recherche ne peut être vide."))
        return HttpResponseRedirect(reverse('campus:who:user-home'))

class RequestUser(View):
    """
    View used get user id using ajax request
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RequestUser, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            # Handling AJAX request for user's autocompletion
            what = request.GET.get('term', '')
            if len(what) < 3:
                raise Http404
            #res = ldap.search(
            #    settings.LDAP_DN_PEOPLE,
            #    '(|(uid=*%(what)s*)(firstname=*%(what)s*)(lastname=*%(what)s*)(displayname=*%(what)s*))' % {'what': what},
            #)
            res = LdapUser.filter(uid__contains=what)
            res += LdapUser.filter(first_name__contains=what)
            res += LdapUser.filter(last_name__contains=what)
            res = list(dict((obj.uid, obj) for obj in res).values())[:20]
            results = []
            if res:
                for user in res:
                    user_json = {}
                    user_json['id'] = user.uid
                    user_json['label'] = '%(firstname)s %(lastname)s (%(uid)s)' % {
                        'firstname': user.first_name,
                        'lastname': user.last_name,
                        'uid': user.uid,
                    }
                    user_json['value'] = user.uid
                    results.append(user_json)
            data = json.dumps(results)
            mimetype = 'application/json'
            return HttpResponse(data, mimetype)

        else:
            raise Http404


class AddPerson(View):
    """
    View used to add godchild
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddPerson, self).dispatch(*args, **kwargs)


    def post(self, request, is_gp):
        #is_gp reports if the user that our beloved user wants to add
        #is a godchild or a godparent

        if is_gp == 'True':
            godparent_uid = request.POST.get('id_user', '')
            godchild_uid = request.user.username
        else:
            godparent_uid = request.user.username
            godchild_uid = request.POST.get('id_user', '')

        try:
            godchild = LdapUser.get(uid=godchild_uid)
            godparent = LdapUser.get(uid=godparent_uid)
        except ObjectDoesNotExist:
            messages.error(request, _("L'utilisateur que vous souhaitez ajouter n'existe pas."))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if godparent.pk == godchild.pk:
            messages.success(request, _("Vous ne pouvez pas vous ajouter vous même."))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if (not godchild.pk in godparent.uid_godchildren) and (not godchild.pk in godparent.uid_godparents):
            godparent.uid_godchildren.append(godchild.pk)
            godparent.save()

        if (not godparent.pk in godchild.uid_godparents) and (not godparent.pk in godchild.uid_godchildren):
            godchild.uid_godparents.append(godparent.pk)
            godchild.save()

        messages.success(request, _("Votre filleul est correctement enregistré."))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class RemovePerson(View):
    """
    View used to remove a godchild
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RemovePerson, self).dispatch(*args, **kwargs)

    def post(self, request, uid, is_gp):
        #is_gp reports if the user that our beloved user wants to remove
        #is a godchild or a godparent

        if is_gp == 'True':
            godparent_uid = uid
            godchild_uid = request.user.username
        else:
            godparent_uid = request.user.username
            godchild_uid = uid

        try:
            godparent = LdapUser.get(uid=godparent_uid)
            godchild = LdapUser.get(uid=godchild_uid)
        except ObjectDoesNotExist:
            messages.error(request, _("L'utilisateur que vous souhaitez supprimer n'existe pas"))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if godchild.pk in godparent.uid_godchildren:
            godparent.uid_godchildren.remove(godchild.pk)
            godparent.save()

        if godparent.pk in godchild.uid_godparents:
            godchild.uid_godparents.remove(godparent.pk)
            godchild.save()

        messages.success(request, _("La modification a été effectuée avec succès"))

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

class ListBirthdays(View):
    """
    View used to list persons that have their birthday today
    """

    template_name = 'campus/whoswho/birthdayList.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ListBirthdays, self).dispatch(*args, **kwargs)

    @staticmethod
    def get_today_birthdays():
        #Since the LDAP don't understand requests without years or something,
        #we have to select people that are between 15 and 35 y/o:
        users = []
        todayDate = today().strftime('%Y%m%d%H%M%S%z')
        todayYear, todayDate = int(todayDate[0:4]), todayDate[4:]
        for year in range(todayYear - 35, todayYear - 15):
            try:
                users += LdapUser.filter(birth_date=str(year)+todayDate)
            except LDAPException as e:
                pass
            except Exception as e:
                pass
        return users

    def get(self, request, *args, **kwarg):
        return render(request, self.template_name, {'users' : self.get_today_birthdays()})
