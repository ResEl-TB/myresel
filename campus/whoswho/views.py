import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View

from campus.forms import MajPersonnalInfo, SearchSomeone

from gestion_personnes.async_tasks import send_mails
from gestion_personnes.models import LdapUser, UserMetaData


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

        user.godchildren = []
        for line in user.uid_godchildren:
            try:
                user.godchildren.append(LdapUser.get(uid=line[4:line.find(',')]))
            except ObjectDoesNotExist:
                pass
        sorted(user.godchildren, key=lambda e: e.first_name + " " + e.last_name.upper())

        user.godparents = []
        for line in user.uid_godparents:
            try:
                user.godparents.append(LdapUser.get(uid=line[4:line.find(',')]))
            except ObjectDoesNotExist:
                pass
        sorted(user.godparents, key=lambda e: e.first_name + " " + e.last_name.upper())

        return render(request, self.template_name, {'display_user' : user})


class UserHome(View):
    """
    View used to see and update user's godparents and
    goddaughter/godson and also search for another user/users
    This is the default view for the whoswho
    """

    #TODO add an option to update godparents/childrens

    template_name = 'campus/whoswho/userHome.html'
    form_class = MajPersonnalInfo

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserHome, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):

        user = request.ldap_user

        form = self.form_class(initial={
            'mail' : user.mail,
            'campus' : user.campus,
            'building' : user.building,
            'room_number' : user.room_number,
            'address' : user.postal_address,
        })

        formSearchUser = SearchSomeone()

        context = {'user': user, 'form': form, 'formSearchUser': formSearchUser}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        formSearchUser = SearchSomeone()
        user = request.ldap_user
        context={'form': form, 'user': user,}

        if form.is_valid():

            mail = form.cleaned_data["mail"]

            if mail != user.mail and len(LdapUser.filter(mail=mail)) > 0:
                form.add_error("email", _("Addresse e-mail déjà utilisée"))
                return render(request, self.template_name, context)

            address = form.cleaned_data["address"]

            if form.cleaned_data["campus"] != "None":
                address = LdapUser.generate_address(form.cleaned_data["campus"], form.cleaned_data["building"], form.cleaned_data["room_number"])

            if user.mail != mail:
                user_meta, __ = UserMetaData.objects.get_or_create(uid=user.uid)
                user_meta.send_email_validation(mail, request.build_absolute_uri)

            #TODO: show_room & show_email
            user.mail = mail
            user.campus = form.cleaned_data["campus"]
            user.building = form.cleaned_data["building"]
            user.room_number = form.cleaned_data["room_number"]
            user.postal_address = address
            user.save()

            messages.success(request, _("Vos Informations ont été mises à jour"))

        context={'user': user, 'form': form, 'formSearchUser': formSearchUser}
        return render(request, self.template_name, context)

class SearchUsers(View):
    """
    View used to search for users
    """

    template_name = 'campus/whoswho/searchUsers.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SearchUsers, self).dispatch(*args, **kwargs)

    #Je passerais en get quand j'aurais pas la flemme
    def post(self, request, *args, **kwargs):

        form = SearchSomeone(request.POST)
        if form.is_valid():
            res = form.getResult(form.cleaned_data["what"])
            if res != False and len(res) != 0:
                return render(request, self.template_name, {'users': res})
            else:
                messages.info(request, _("La recherche n'a rien retourné"))
        else:
            messages.error(request, _("Le contenue de la recherche ne peut être vide."))
        return redirect('campus:who:user-home')

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
            res = set()
            res |= set(LdapUser.filter(uid__contains=what))
            res |= set(LdapUser.filter(first_name__contains=what))
            res |= set(LdapUser.filter(last_name__contains=what))
            res = list(res)[:20]
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


class AddBizu(View):
    """
    View used to add godchild
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AddBizu, self).dispatch(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        try:
            godchild = LdapUser.get(uid=request.POST.get('id_user', ''))
        except ObjectDoesNotExist:
            messages.error(request, _("L'utilisateur que vous souhaitez ajouter comme filleul n'existe pas."))
            return HttpResponseRedirect(reverse('campus:who:user-details', args=[request.user.username]))

        godparent = LdapUser.get(uid=request.user.username)

        if godparent.pk == godchild.pk:
            messages.success(request, _("Vous ne pouvez pas vous ajouter vous même."))
            return HttpResponseRedirect(reverse('campus:who:user-details', args=[request.user.username]))

        if not godchild.pk in godparent.uid_godchildren :
            godparent.uid_godchildren.append(godchild.pk)
            godparent.save()

        if not godparent.pk in godchild.uid_godparents :
            godchild.uid_godparents.append(godparent.pk)
            godchild.save()

        messages.success(request, _("Votre filleul est correctement enregistré."))
        return HttpResponseRedirect(reverse('campus:who:user-details', args=[request.user.username]))
