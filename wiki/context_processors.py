from .models import Category

def articles_in_menu(request):
    """
    Context processors pour générer les catégories et leurs articles dans la navbar
    """

    categories = Category.objects.all().order_by('-priority')
    
    return {'categories': categories}

 
