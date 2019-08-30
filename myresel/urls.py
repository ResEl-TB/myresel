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
from pages.views import Home, Contact, NewsListe, FaqList, faqVote, NewsDetail, Services, \
    unsecure_set_language, NewsRSS, NewsAtom, StatusPageXhr, eggdrop, Television

from myresel import settings


js_info_dict = {
    'packages': ('tresorerie',),
}

urlpatterns = [
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),

    url(r'^lang/setlang/$', unsecure_set_language, name='set_language'),
    url(r'^lang/', include('django.conf.urls.i18n')),

    url(r'^login', auth_views.login, name='login'),
    url(r'^logout', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^gestion/django-rq/', include('django_rq.urls')),
    url(r'^gestion/', admin.site.urls),

    url(r'^personnes/', include('gestion_personnes.urls', namespace='gestion-personnes')),
    url(r'^paiement/', include('tresorerie.urls', namespace='tresorerie')),
    url(r'^tarifs/', RedirectView.as_view(pattern_name="tresorerie:prices", permanent=False)),

    url(r'^wiki/', include('wiki.urls', namespace='wiki')),
    url(r'^news/$', NewsListe.as_view(), name='news'),
    url(r'^news/(?P<pk>\d+)$', NewsDetail.as_view(), name='piece-of-news'),
    url(r'^rss-news$', NewsRSS(), name="rss"),
    url(r'^atom-news$', NewsAtom(), name="atom"),
    url(r'^faq/$', FaqList.as_view(), name='faq'),
    url(r'^faq/upvote/$', faqVote, name='upvote'),
    url(r'^contact/', Contact.as_view(), name='contact'),
    url(r'^mentions_legales/', TemplateView.as_view(template_name='pages/mentions_legales.html'), name="mentions_legales"),
    url(r'^services/', Services.as_view(), name='services'),
    url(r'^campus/', include('campus.urls', namespace='campus')),
    url(r'^eggdrop/$', eggdrop, name='eggdrop-default'),
    url(r'^eggdrop/(?P<channel>\w+)/$', eggdrop, name='eggdrop-channel'),
    url(r'^eggdrop/(?P<channel>\w+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$', eggdrop, name='eggdrop-date'),

    url(r'^favicon.ico', RedirectView.as_view(url='/static/images/icons/favicon-96x96.png', permanent=False), name="favicon"),

    url(r'^inscription_zone/', inscription_zone_info, name="inscription-zone"),

    url(r'^tv', Television.as_view(), name="tv-index"),
    url(r'^help-needed/', TemplateView.as_view(template_name='help_needed.html'), name="help-needed"),
    url(r'^how-to-signup', TemplateView.as_view(template_name='pages/how_to_signup.html'), name="how-to-signup"),
    url(r'^become/$', TemplateView.as_view(template_name='pages/become_admin.html'), name='become-admin'),
    url(r'^status/$', TemplateView.as_view(template_name='pages/network_status.html'), name='network-status'),
    url(r'^wp-login.php$', TemplateView.as_view(template_name='418.html'), name='418'),

    # FIXME: For the moment we keep the API here, in the future we might make that
    # cleaner
    url(r'^_api/v1/status/$', StatusPageXhr.as_view(), name='network-status-xhr'),

    url(r'^$', Home.as_view(), name='home'),



]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]

handler400 = 'myresel.error_views.bad_request'
handler403 = 'myresel.error_views.permission_denied'
handler404 = 'myresel.error_views.page_not_found'
handler500 = 'myresel.error_views.server_error'
