from django.conf import settings
from django.contrib.auth.models import User

from fonctions import ldap

class DatMiddleware(object):
    def process_request(self, request):
        # Check if the user is a ResEl admin. If so, it's credentials will be updated to superuser and staff
        if request.user.is_authenticated():
            res = ldap.search(settings.LDAP_ADMIN, '(&(uid=%s))' % request.user.username)
            if len(res) == 1:
                user = User.objects.get(username=request.user.username)
                user.is_staff = 1
                user.is_superuser = 1
                user.save()
