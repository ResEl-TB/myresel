from django.conf.urls import url, include

urlpatterns = [
    url(r'^salles/', include('campus.suburls.urls_rooms', namespace='rooms')),
]