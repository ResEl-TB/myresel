"""tresorerie URL Configuration
"""

from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^$', ChooseProduct.as_view(), name='home'),
    url(r'^tarifs/$', ListProducts.as_view(), name='prices'),
    url(r'^acheter/(?P<product_id>[0-9]+)', Pay.as_view(), name='pay'),
    url(r'^historique/$', History.as_view(), name='historique'),
    url(r'^transaction/(?P<slug>[-\w]+)/$', TransactionDetailView.as_view(), name='transaction-detail'),
]