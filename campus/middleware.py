# -*- coding: utf-8 -*-
"""
Middlewares for campus module
"""
from django.core.urlresolvers import resolve

from campus.models import StudentOrganisation, RoomAdmin, Room

class RoomAdminMiddleware(object):
    """
    Check if user is a RoomAdmin, and updates his credentials accordingly
    """

    @staticmethod
    def process_request(request):
        """
        Do the room checking then update user credentials
        Should only be called by Django
        
        :param request: 
        :return: None
        """
        # TODO: this method is not actually working...
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
            for club in StudentOrganisation.all():
                if request.ldap_user.uid in '\t'.join(club.prezs):
                    clubs.append(club)
                    is_prez = True

            if not RoomAdmin.objects.filter(user__pk=request.user.pk) and is_prez:
                admin = RoomAdmin()
                admin.user = request.user
                admin.save()

                for club in clubs:
                    for room in Room.objects.filter(clubs__contains=club.cn):
                        admin.rooms.add(room)

            else:
                # User is Admin, check if he still is
                admin = RoomAdmin.objects.get(user__pk=request.user.pk)
                if is_prez:
                    admin.rooms.clear()
                    for club in clubs:
                        for room in Room.objects.filter(clubs__contains=club.cn):
                            admin.rooms.add(room)
                else:
                    admin.delete()
