"""myresel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.views.i18n import javascript_catalog
from pages.views import Home, Contact, NewsListe, inscriptionZoneInfo, FaqList, faqUpvote, NewsDetail
from myresel import settings


js_info_dict = {
    'packages': ('tresorerie',),
}

urlpatterns = [
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^lang/', include('django.conf.urls.i18n')),

    url(r'^login', auth_views.login, name='login'),
    url(r'^logout', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^gestion/django-rq/', include('django_rq.urls')),
    url(r'^gestion/', admin.site.urls),

    url(r'^machines/', include('devices.urls', namespace='gestion-machines')),
    url(r'^personnes/', include('gestion_personnes.urls', namespace='gestion-personnes')),
    url(r'^paiement/', include('tresorerie.urls', namespace='tresorerie')),

    url(r'^wiki/', include('wiki.urls', namespace='wiki')),
    url(r'^news/$', NewsListe.as_view(), name='news'),
    url(r'^news/(?P<pk>\d+)$', NewsDetail.as_view(), name='piece-of-news'),
    url(r'^faq/$', FaqList.as_view(), name='faq'),
    url(r'^faq/upvote/$', faqUpvote, name='upvote'),
    url(r'^contact/', Contact.as_view(), name='contact'),
    url(r'^campus/', include('campus.urls', namespace='campus')),

    # Subcription related urls
    url(r'^inscription_zone/', inscriptionZoneInfo, name="inscription-zone"),
    url(r'^generate_204/', RedirectView.as_view(pattern_name="inscription-zone", permanent=False), name="generate_204"),

    url(r'^help-needed/', TemplateView.as_view(template_name='help_needed.html'), name="help-needed"),

    url(r'^$', Home.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'myresel.error_views.bad_request'
handler403 = 'myresel.error_views.permission_denied'
handler404 = 'myresel.error_views.page_not_found'
handler500 = 'myresel.error_views.server_error'
