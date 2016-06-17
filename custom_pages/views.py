from django.shortcuts import render
from .models import Category, Article
from django.views.generic import DetailView, ListView
from django.utils.translation import ugettext_lazy as _


class CategoryView(DetailView):
    model = Category
    template_name = 'custom_pages/show-category.html'


class ArticleView(DetailView):
    model = Article
    template_name = 'custom_pages/show-article.html'

