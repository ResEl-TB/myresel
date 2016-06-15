from django.contrib import admin
from django.contrib.auth.models import Group, User
from modeltranslation.admin import TranslationAdmin
from .models import News

class NewsAdmin(TranslationAdmin):
    pass

admin.site.register(News, NewsAdmin)

admin.site.unregister(User)
admin.site.unregister(Group)