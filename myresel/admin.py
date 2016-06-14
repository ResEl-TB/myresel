from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import *

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(Billet)