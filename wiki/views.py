from django.views.generic import DetailView

from .models import Category, Article


class CategoryView(DetailView):
    model = Category
    template_name = 'wiki/show-category.html'


class ArticleView(DetailView):
    model = Article
    template_name = 'wiki/show-article.html'
