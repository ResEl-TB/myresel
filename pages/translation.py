from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from pages.models import News, Faq


@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)

@register(Faq)
class FaqTranslationOptions(TranslationOptions):
    fields = ('question_text', 'response',)
