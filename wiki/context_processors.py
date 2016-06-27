from django.conf import settings
from .models import Category

NB_ARTICLES_TO_DISPLAY_IN_SUBMENU = 5 # TODO : refactor this

def articles_in_menu(request):
    """Fonction pour générer les catégories et leurs articles dans la navbar

    Appellée automatiquement en tant que context processor
    """
    categories = Category.objects.all().order_by('-id')
    # Good to know : django's queryset are lazy, so by slicing, not all results are asked
    
    return {'categories': categories, 'nbArticlesToDisplay': NB_ARTICLES_TO_DISPLAY_IN_SUBMENU, 'nbArticlesSlicer': ":"+str(NB_ARTICLES_TO_DISPLAY_IN_SUBMENU)}

 
