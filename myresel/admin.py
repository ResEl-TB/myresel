from django.contrib import admin
from django.contrib.auth.models import Group, User

admin.site.unregister(User)
admin.site.unregister(Group)

