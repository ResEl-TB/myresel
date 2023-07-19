from modeltranslation.translator import register, TranslationOptions

from .models import Article, Category, Link


@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'text',)


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(Link)
class LinkTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

