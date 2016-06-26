from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pages.models import News


class NewsAdmin(TranslationAdmin):
    pass


admin.site.register(News, NewsAdmin)