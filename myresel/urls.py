"""myresel URL Configuration """

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from pages.views import Home, Contact, NewsListe, inscription_zone_info, captive_portal_api, \
    FaqList, faqVote, NewsDetail, Services, unsecure_set_language, NewsRSS, NewsAtom, \
    StatusPageXhr, eggdrop, Television, graph_api

from myresel import settings

js_info_dict = {
    'packages': ('tresorerie',),
}

login_forbidden =  user_passes_test(lambda u: u.is_anonymous, '/', redirect_field_name=None)

urlpatterns = [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), js_info_dict, name='javascript-catalog'),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),

    url(r'^lang/setlang/$', unsecure_set_language, name='set_language'),
    url(r'^lang/', include('django.conf.urls.i18n')),

    url(r'^login', login_forbidden(auth_views.LoginView.as_view()), name='login'),
    url(r'^logout', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    url(r'^gestion/django-rq/', include('django_rq.urls')),
    url(r'^gestion/', admin.site.urls),

    url(r'^machines/', include('devices.urls', namespace='gestion-machines')),
    url(r'^personnes/', include('gestion_personnes.urls', namespace='gestion-personnes')),
    url(r'^maisel/', include('maisel.urls', namespace='maisel')),
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
    url(r'^captive-portal/api', captive_portal_api, name="captive-portal-api"),

    url(r'^tv', Television.as_view(), name="tv-index"),
    url(r'^help-needed/', TemplateView.as_view(template_name='help_needed.html'), name="help-needed"),
    url(r'^how-to-signup', TemplateView.as_view(template_name='pages/how_to_signup.html'), name="how-to-signup"),
    url(r'^become/$', TemplateView.as_view(template_name='pages/become_admin.html'), name='become-admin'),
    url(r'^status/$', TemplateView.as_view(template_name='pages/network_status.html'), name='network-status'),
    url(r'^wp-login.php$', TemplateView.as_view(template_name='418.html'), name='418'),

    url(r'^graph/api/v0/exec$', graph_api, name='graph-api'),

    # FIXME: For the moment we keep the API here, in the future we might make that
    # cleaner
    url(r'^_api/v1/status/$', StatusPageXhr.as_view(), name='network-status-xhr'),

    url(r'^$', Home.as_view(), name='home'),



]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
