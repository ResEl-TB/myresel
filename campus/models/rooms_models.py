from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

import django_rq
from datetime import timedelta

from gestion_personnes.models import LdapUser
import campus.async_tasks as async_tasks
from campus.models.clubs_models import StudentOrganisation

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

    clubs = models.TextField(
        verbose_name='club(s)',
        help_text=_('indique à quel(s) club(s) appartient la salle, un par ligne'),
        blank=True,
    )

    def user_can_access(self, user):
        """ Checks if a user can access the room """

        if self.private:
            granted = False
            for club in self.get_clubs():
                if (user.uid in '\t'.join(club.members)) or (user.uid in '\t'.join(club.prezs)):
                    granted = True
                    break
        else:
            granted = True
        return granted

    def user_can_manage(self, user):
        """ Checks if a user can manage bookings for this room """

        granted = False
        if self.private:
            for club in self.get_clubs():
                if user.uid in '\t'.join(club.prezs):
                    granted = True
                    break
        return granted

    def get_clubs(self):
        """ Get allowed clubs for the room """

        clubs = []
        if self.private:
            clubs = list()
            for club_cn in self.clubs.split('\r\n'):
                try:
                    clubs.append(StudentOrganisation.get(pk=club_cn))
                except ObjectDoesNotExist:
                    pass
        return clubs

    def __str__(self):
        return '%s - %s' % (self.name, self.get_location_display())

    def is_free(self, start_date, end_date):
        """ Checks if a room is free between the time range given """

        return self.roombooking_set.filter(
            start_time__lt=end_date,
            end_time__gt=start_date
        ).count() == 0


class RoomBookingManager(models.Manager):
    """
    Custom Manager for RoomBooking object

    Because some dates methods are hard, so we implement them once for all here.
    """
    def in_date_range(self, start, end, *args, **kwargs):
        return self.filter(
            start_time__year=start,
            start_time__month=end,
            *args,
            **kwargs
        )

class RoomBooking(models.Model):
    class Meta:
        verbose_name = _('réservation')

    objects = RoomBookingManager()

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

    RECURRING_CHOICES = (
        ('NONE', _("Pas de récurrence")),
        ('DAILY', _("Quotidient")),
        ('WEEKLY', _("Hebdomadaire")),
        ('MONTHLY', _("Mensuel")),
        ('ANNUALLY', _("Annuel")),
    )

    STATUS_CHOICES = (
        ('NEW', _("Non validé")),
        ('VALIDATED', _("Validé")),
        ('REFUSED', _("Refusé")),
        ('DELETED', _("Supprimé")),
    )

    description = models.TextField(
        help_text=_('description de l\'évènement'),
    )

    room = models.ManyToManyField(
        'Room',
        db_index=True,
        help_text=_('indique dans quelle salle se déroule l\'évènement'),
        verbose_name=_('Salle(s)'),
    )

    start_time = models.DateTimeField(
        db_index=True,
        help_text=_('début de l\'évènement'),
        verbose_name=_('Début de l\'evènement'),
    )

    end_time = models.DateTimeField(
        db_index=True,
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

    recurring_rule = models.CharField(
        choices=RECURRING_CHOICES,
        help_text=_('Type de recurrence'),
        default='NONE',
        max_length=10,
    )

    end_recurring_period = models.DateTimeField(
        verbose_name=_("fin de la récurrence"),
        null=True, blank=True, db_index=True,
        help_text=_("Cette date est ignorée pour les événements uniques.")
    )

    status = models.TextField(
        choices=STATUS_CHOICES,
        max_length=15,
        default="NEW",
        help_text=_('Statut'),
    )

    # If the event belongs to an organisation (club or association)
    organisation = models.TextField(
        max_length=60,
        null=True,
        blank=True,
    )

    def get_occurences(self):
        if self.recurring_rule == 'NONE':
            return [self.start_time]
        else:
            delta = {
                'DAILY': relativedelta(days=1),
                'WEEKLY': relativedelta(weeks=1),
                'MONTHLY': relativedelta(months=1),
                'ANNUALLY': relativedelta(years=1),
            }
            # TODO: make a test to check if this condition is executed
            if self.end_recurring_period is None:
                return [self.start_time]

            occurrences = []
            current_occ = self.start_time
            while current_occ <= self.end_recurring_period:
                occurrences.append(current_occ)
                current_occ = current_occ + delta[self.recurring_rule]
            return occurrences

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

    def user_can_manage(self, user):
        """
        Tells if a user can manage this Booking
        :param user: LdapUser to check
        :return: True or False
        """
        # User can manage reservations for this room
        for room in self.room.all():
            if room.user_can_manage(user):
                return True

        # User can modify his own reservation
        return user.uid == self.user

class RoomAdmin(models.Model):
    class Meta:
        verbose_name = 'administrateur des salles'
        verbose_name_plural = 'administrateurs des salles'

    user = models.ForeignKey(
        User,
        verbose_name='utilisateur',
    )

    rooms = models.ManyToManyField(
        'Room',
        verbose_name='Salles accessibles',
    )

    def __str__(self):
        return self.user.username