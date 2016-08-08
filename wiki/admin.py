from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pages.admin import NewsAdmin
from pages.models import News
from .models import Article, Category, Link


class CategoryAdmin(TranslationAdmin):
    pass


class ArticleAdmin(TranslationAdmin):
    pass


class LinkAdmin(TranslationAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Link, LinkAdmin)