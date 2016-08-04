from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from pages.models import News


@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)