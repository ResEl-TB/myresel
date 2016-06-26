from django.conf import settings
from .models import Category

def articles_in_menu(request):
    categories = Category.objects.all().order_by('-id')
    return {'categories': categories}

