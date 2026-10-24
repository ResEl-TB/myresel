"""tresorerie URL Configuration
"""

from django.urls import re_path

from .views import *

app_name = 'tresorerie'

urlpatterns = [
    re_path(r'^$', ChooseProduct.as_view(), name='home'),
    re_path(r'^tarifs/$', ListProducts.as_view(), name='prices'),
    re_path(r'^acheter/(?P<product_id>[0-9]+)', Pay.as_view(), name='pay'),
    re_path(r'^historique/$', History.as_view(), name='historique'),
    re_path(r'^transaction/(?P<slug>[-\w]+)/$', TransactionDetailView.as_view(), name='transaction-detail'),
]
