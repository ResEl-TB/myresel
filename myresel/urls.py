"""myresel URL Configuration """

from django.urls import include, re_path
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
    re_path(r'^jsi18n/$', JavaScriptCatalog.as_view(), js_info_dict, name='javascript-catalog'),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),

    re_path(r'^lang/setlang/$', unsecure_set_language, name='set_language'),
    re_path(r'^lang/', include('django.conf.urls.i18n')),

    re_path(r'^login', login_forbidden(auth_views.LoginView.as_view()), name='login'),
    re_path(r'^logout', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'^gestion/django-rq/', include('django_rq.urls')),
    re_path(r'^gestion/', admin.site.urls),

    re_path(r'^machines/', include('devices.urls', namespace='gestion-machines')),
    re_path(r'^personnes/', include('gestion_personnes.urls', namespace='gestion-personnes')),
    re_path(r'^maisel/', include('maisel.urls', namespace='maisel')),
    re_path(r'^paiement/', include('tresorerie.urls', namespace='tresorerie')),
    re_path(r'^tarifs/', RedirectView.as_view(pattern_name="tresorerie:prices", permanent=False)),

    re_path(r'^wiki/', include('wiki.urls', namespace='wiki')),
    re_path(r'^news/$', NewsListe.as_view(), name='news'),
    re_path(r'^news/(?P<pk>\d+)$', NewsDetail.as_view(), name='piece-of-news'),
    re_path(r'^rss-news$', NewsRSS(), name="rss"),
    re_path(r'^atom-news$', NewsAtom(), name="atom"),
    re_path(r'^faq/$', FaqList.as_view(), name='faq'),
    re_path(r'^faq/upvote/$', faqVote, name='upvote'),
    re_path(r'^contact/', Contact.as_view(), name='contact'),
    re_path(r'^discord/', RedirectView.as_view(url="https://discord.gg/A3xYnC4uh5", permanent=False)),
    re_path(r'^mentions_legales/', TemplateView.as_view(template_name='pages/mentions_legales.html'), name="mentions_legales"),
    re_path(r'^services/', Services.as_view(), name='services'),
    re_path(r'^eggdrop/$', eggdrop, name='eggdrop-default'),
    re_path(r'^eggdrop/(?P<channel>\w+)/$', eggdrop, name='eggdrop-channel'),
    re_path(r'^eggdrop/(?P<channel>\w+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$', eggdrop, name='eggdrop-date'),

    re_path(r'^favicon.ico', RedirectView.as_view(url='/static/images/icons/favicon-96x96.png', permanent=False), name="favicon"),

    re_path(r'^inscription_zone/', inscription_zone_info, name="inscription-zone"),

    re_path(r'^tv', Television.as_view(), name="tv-index"),
    re_path(r'^help-needed/', TemplateView.as_view(template_name='help_needed.html'), name="help-needed"),
    re_path(r'^how-to-signup', TemplateView.as_view(template_name='pages/how_to_signup.html'), name="how-to-signup"),
    re_path(r'^become/$', TemplateView.as_view(template_name='pages/become_admin.html'), name='become-admin'),
    re_path(r'^status/$', TemplateView.as_view(template_name='pages/network_status.html'), name='network-status'),
    re_path(r'^wp-login.php$', TemplateView.as_view(template_name='418.html'), name='418'),

    re_path(r'^graph/api/v0/exec$', graph_api, name='graph-api'),

    # FIXME: For the moment we keep the API here, in the future we might make that
    # cleaner
    re_path(r'^_api/v1/status/$', StatusPageXhr.as_view(), name='network-status-xhr'),
    re_path(r'^_api/v1/captive-portal', captive_portal_api, name="captive-portal-api"),

    re_path(r'^$', Home.as_view(), name='home'),



]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [re_path(r'^__debug__/', include(debug_toolbar.urls))]
