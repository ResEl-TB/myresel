from django.shortcuts import render
from .models import Category, Article
from django.views.generic import DetailView, ListView
from django.utils.translation import ugettext_lazy as _


class CategoryView(DetailView):
    model = Category

class ArticleView(DetailView):
    model = Article
    

