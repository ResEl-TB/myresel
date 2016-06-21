from django.contrib import admin
from django.db import models
from .models import Article, Category, News
from modeltranslation.admin import TranslationAdmin


class CategoryAdmin(TranslationAdmin):
    pass


class ArticleAdmin(TranslationAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)


class NewsAdmin(TranslationAdmin):
    pass

admin.site.register(News, NewsAdmin)