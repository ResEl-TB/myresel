from django.contrib import admin
from django.db import models
from .models import Article, Category

admin.site.register(Article)
admin.site.register(Category)
