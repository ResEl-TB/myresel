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
from django.urls import re_path

from gestion_personnes.views import ResetPwd, CheckEmail
from .views import Inscription, ModPasswd, InscriptionCGU, Settings
from .views import PersonalInfo, ResetPwdSend, SendUid, MailResEl, DeleteMailResEl, RedirectMailResEl, Webmail

app_name = 'gestion_personnes'

urlpatterns = [
    re_path(r'^inscription$', Inscription.as_view(), name='inscription'),
    re_path(r'^cgu$', InscriptionCGU.as_view(), name='cgu'),
    re_path(r'^modification-passwd$', ModPasswd.as_view(), name='mod-passwd'),
    re_path(r'^parametres$', Settings.as_view(), name='settings'),
    re_path(r'^mail$', MailResEl.as_view(), name='mail'),
    re_path(r'^mail/delete$', DeleteMailResEl.as_view(), name='delete-mail'),
    re_path(r'^webmail$', Webmail.as_view(), name='webmail'),
    re_path(r'^mail/redirect$', RedirectMailResEl.as_view(), name='redirect-mail'),
    re_path(r'^reset-pwd/(?P<key>[-\w]+)$', ResetPwd.as_view(), name='reset-pwd'),
    re_path(r'^reset-pwd$', ResetPwdSend.as_view(), name='reset-pwd-send'),
    re_path('^send-uid$', SendUid.as_view(), name='send-uid'),
    re_path('^check-email$', CheckEmail.as_view(), name='check-email'),
    re_path('^check-email/(?P<key>[-\w]+)$', CheckEmail.as_view(), name='check-email'),
    re_path(r'^$', PersonalInfo.as_view(), name='personal-infos'),
]
