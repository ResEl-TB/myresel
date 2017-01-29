from django.core.urlresolvers import resolve

from campus.models import Club, RoomAdmin, Room

class RoomAdminMiddleware(object):
    """
    Check if user is a RoomAdmin, and updates his credentials accordingly
    """

    def process_request(self, request):

        # It is not possible to view any page if the user is not logged in
        try:
            request.ldap_user
        except AttributeError:
            return

        if request.ldap_user.uid == 'pbouilla':
            # Pbouilla is admin <3
            pass

        elif resolve(request.META['PATH_INFO']).view_name == 'campus:rooms:booking':
            is_prez = False
            clubs = list()
            for c in Club.all():
                if request.ldap_user.uid in '\t'.join(c.prezs):
                    clubs.append(c) 
                    is_prez = True

            if not RoomAdmin.objects.filter(user__pk=request.user.pk) and is_prez:
                a = RoomAdmin()
                a.user = request.user
                a.save()

                for club in clubs:
                    for room in Room.objects.filter(clubs__contains=club.cn):
                        a.rooms.add(room)

            else:
                # User is Admin, check if he still is
                a = RoomAdmin.objects.get(user__pk=request.user.pk)
                if is_prez:
                    a.rooms.clear()
                    for club in clubs:
                        for room in Room.objects.filter(clubs__contains=club.cn):
                            a.rooms.add(room)
                else:
                    a.delete()