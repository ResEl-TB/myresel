"""gestion_personnes URL Configuration

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
from django.conf.urls import url

from gestion_personnes.views import ResetPwd, CheckEmail
from .views import Inscription, ModPasswd, InscriptionCGU, Settings
from .views import PersonalInfo, ResetPwdSend, SendUid, MailResEl, DeleteMailResEl, RedirectMailResEl

urlpatterns = [
    url(r'^inscription$', Inscription.as_view(), name='inscription'),
    url(r'^cgu$', InscriptionCGU.as_view(), name='cgu'),
    url(r'^modification-passwd$', ModPasswd.as_view(), name='mod-passwd'),
    url(r'^parametres$', Settings.as_view(), name='settings'),
    url(r'^mail$', MailResEl.as_view(), name='mail'),
    url(r'^mail/delete$', DeleteMailResEl.as_view(), name='delete-mail'),
    url(r'^mail/redirect$', RedirectMailResEl.as_view(), name='redirect-mail'),
    url(r'^reset-pwd/(?P<key>[-\w]+)$', ResetPwd.as_view(), name='reset-pwd'),
    url(r'^reset-pwd$', ResetPwdSend.as_view(), name='reset-pwd-send'),
    url('^send-uid$', SendUid.as_view(), name='send-uid'),
    url('^check-email$', CheckEmail.as_view(), name='check-email'),
    url('^check-email/(?P<key>[-\w]+)$', CheckEmail.as_view(), name='check-email'),
    url(r'^$', PersonalInfo.as_view(), name='personal-infos'),
]
