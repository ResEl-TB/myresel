from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pages.admin import NewsAdmin
from pages.models import News
from .models import Article, Category


class CategoryAdmin(TranslationAdmin):
    pass


class ArticleAdmin(TranslationAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
