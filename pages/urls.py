
from django.conf.urls import url
from pages.views import NewsListe

urlpatterns = [
    url(r'^news/', NewsListe.as_view(), name='news'),
    ]