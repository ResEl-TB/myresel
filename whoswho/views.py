from django.shortcuts import render
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.views.generic import View
from .models import UserModel

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
    
    def get(self, request, uid):
        user = UserModel.get(uid=uid)
        return render(request, self.template_name, {'user' : user})
    