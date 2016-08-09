from django.shortcuts import render
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import Http404
from gestion_personnes.models import LdapUser
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class Godparents(View):
    """
    View used to see and update user's godparents and
    goddaughter/godson
    """
    
    template_name = 'whoswho/godparents.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
        

class UserDetails(View):
    """
    View used to see and update user's godparents and
    goddaughter/godson
    """
    
    template_name = 'whoswho/userDetails.html'
    
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
                user.godchildren.append(LdapUser.get(line[4:find(line,',')]))
            except ObjectDoesNotExist:
                pass
            
        user.godparents = []
        for line in user.uid_godparents:
            try:
                user.godparents.append(LdapUser.get(line[4:find(line,',')]))
            except ObjectDoesNotExist:
                pass
        
        return render(request, self.template_name, {'user' : user})
    