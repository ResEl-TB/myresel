from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pages.models import News


class NewsAdmin(TranslationAdmin):

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'author', None) is None:
            obj.author = request.user
        obj.save()

admin.site.register(News, NewsAdmin)