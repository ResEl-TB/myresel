from modeltranslation.translator import translator, TranslationOptions
from news.models import Article, Category

@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'text',)

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)
