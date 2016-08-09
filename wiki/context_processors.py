from .models import Category

def articles_in_menu(request):
    """
    Context processors pour générer les catégories et leurs articles dans la navbar
    """

    categories = Category.objects.all().order_by('-priority')
    # TODO :
    # Select articles and links here,
    # because we cant tell if is in resel in template
    # so can't load article that show only if in resel

    return {'categories': categories}

 
