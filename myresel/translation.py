from modeltranslation.translator import register, TranslationOptions
from myresel.models import News

@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('titre', 'contenu',)