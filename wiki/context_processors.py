from django.conf import settings
from .models import Category
from myresel.constantes import NB_ARTICLES_TO_DISPLAY_IN_SUBMENU

def articles_in_menu(request):
    """Fonction pour générer les catégories et leurs articles dans la navbar

    Appellée automatiquement en tant que context processor
    """
    categories = Category.objects.all().order_by('-id')
    return {'categories': categories[:NB_ARTICLES_TO_DISPLAY_IN_SUBMENU], 'nbCategories': len(categories)}

