from django.db import models
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group
from django.db.models import Q

import django_rq
from datetime import timedelta

from gestion_personnes.models import LdapUser
import campus.async_tasks as async_tasks

class Room(models.Model):
    class Meta:
        verbose_name = _('salle')

    LOCATIONS = (
        ('F', _('Foyer')),
        ('S', _('École')),
        ('O', _('Extérieur')),
        ('C', _('Campus')),
    )

    location = models.CharField(
        max_length=1,
        choices=LOCATIONS,
        help_text=_('emplacement de la salle'),
        verbose_name=_('Emplacement'),
    )

    name = models.CharField(
        max_length=20,
        help_text=_('nom de la salle'),
        verbose_name=_('Nom de la salle'),
    )

    mailing_list = models.EmailField(
        blank=True,
        help_text=_('mailing-list à contacter pour réserver cette salle'),
    )

    private = models.BooleanField(
        help_text=_('indique si la salle est privée ou non'),
        default=False,
        verbose_name=_('Salle privée / club'),
    )

    allowed_members = models.TextField(
        help_text=_('indique les utilisateurs pouvant réserver la salle, un par ligne'),
        blank=True,
        verbose_name=_('Membres authorisés'),
    )

    def __str__(self):
        return '%s - %s' % (self.name, self.get_location_display()) 

    def is_free(self, start_date, end_date):
        """ Checks if a room is free between the time range given """
        
        events = RoomBooking.objects.filter(
            room__pk=self.pk,
            start_time__year=start_date.year,
            start_time__month=start_date.month,
            start_time__day=start_date.day,
        )
        print(events)

        free = True
        for event in events:
            if event.start_time <= start_date <= event.end_time or event.start_time <= end_date <= event.end_time:
                free = False
                break
        return free

class RoomBooking(models.Model):
    class Meta:
        verbose_name = _('réservation')

    BOOKING_TYPES = (
        ('party', _('Soirée')),
        ('club', _('Activité de club')),
        ('meeting', _('Réunion')),
        ('training', _('Formation')),
        ('event', _('Évènement')),
        ('sport', _('Sport')),
        ('arts', _('Art et culture')),
        ('trip', _('Sortie')),
        ('other', _('Autre')),
        ('hidden', _('Ne pas afficher sur le calendrier')),
    )

    description = models.TextField(
        help_text=_('description de l\'évènement'),
    )

    room = models.ManyToManyField(
        'Room',
        help_text=_('indique dans quelle salle se déroule l\'évènement'),
        verbose_name=_('Salle(s)'),
    )

    start_time = models.DateTimeField(
        help_text=_('début de l\'évènement'),
        verbose_name=_('Début de l\'evènement'),
    )

    end_time = models.DateTimeField(
        help_text=_('fin de l\'évènement'),
        verbose_name=_('Fin de l\'évènement'),
    )

    user = models.CharField(
        max_length=50,
        help_text=_('utilisateur ayant fait la demande de réservation'),
        verbose_name=_('Utilisateur'),
    )

    booking_type = models.CharField(
        max_length=50,
        choices=BOOKING_TYPES,
        help_text=_('type d\'évènement'),
        verbose_name='Type', 
    )

    displayable = models.BooleanField(
        help_text=_('affiche ou non cet évènement sur le calendrier'),
        default=True,
        verbose_name=_('Affichable'),
    )

    def __str__(self):
        return '%s - %s' % (self.description, self.start_time.strftime('Début le %d %B %Y à %H:%M'))

    def notify_mailing_list(self):
        queue = django_rq.get_queue()
        for room in self.room.all():
            if room.location == 'S':
                queue.enqueue_call(
                    async_tasks.notify_mailing_list,
                    args=(LdapUser.get(pk=self.user), room),
                )

class RoomAdmin(models.Model):
    class Meta:
        verbose_name = 'administrateur des salles'
        verbose_name_plural = 'administrateurs des salles'

    uid = models.CharField(
        max_length=15,
        verbose_name='nom d\'utilisateur',
    )