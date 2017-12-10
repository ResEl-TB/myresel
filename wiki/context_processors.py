from .models import Category
from django.core.exceptions import ObjectDoesNotExist
from fonctions.decorators import robust_cache

@robust_cache()
def _load_articles_in_menu():
    categories = Category.objects.all().order_by('-priority')

    try:
        association_category = Category.objects.get(slug='lassociation')
    except ObjectDoesNotExist:
        association_category = None

    try:
        services_category = Category.objects.get(slug='services')
    except ObjectDoesNotExist:
        services_category = None
    return categories.values(), association_category, services_category

def articles_in_menu(request):
    """
    Context processors pour générer les catégories et leurs articles dans la navbar
    """
    categories, association_category, services_category = _load_articles_in_menu()

    return {
        'categories': categories,
        'association_category': association_category,
        'services_category': services_category,
    }


