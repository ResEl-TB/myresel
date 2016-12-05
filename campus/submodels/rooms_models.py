from django.db import models
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _

from datetime import timedelta

from gestion_personnes.models import LdapUser

class Room(models.Model):
    LOCATIONS = (
        ('F', _('Foyer')),
        ('S', _('École')),
    )

    location = models.CharField(
        max_length=1,
        choices=LOCATIONS,
        help_text=_('emplacement de la salle'),
    )

    name = models.CharField(
        max_length=20,
        help_text=_('nom de la salle'),
    )

    mailing_list = models.EmailField(
        blank=True,
        help_text=_('mailing-list à contacter pour réserver cette salle'),
    )

    private = models.BooleanField(
        help_text=_('indique si la salle est privée ou non'),
        default=False,
    )

    def is_free(self, start_date, end_date):
        """ Checks if a room is free between the time range given """
        events = self.roombooking_set.all() \
            .filter(start_time__range=(start_date, start_date + timedelta(days=1)))
        free1 = True
        for e in events:
            if e.start_time <= start_date <= e.end_time:
                free1 = False
                break

        events = self.roombooking_set.all() \
            .filter(end_time__range=(end_date, end_date + timedelta(days=1)))
        free2 = True
        for e in events:
            if e.start_time <= end_date <= e.end_time:
                free2 = False
                break

        return free1 and free2

class RoomBooking(models.Model):
    class META:
        permissions = (
            ('can_moderate', 'Indique si l\'admin peut modérer ou non les réservations de salle'),
        )

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
    
    name = models.CharField(
        max_length=20,
        help_text=_('nom de l\'évènement'),
    )

    description = models.TextField(
        help_text=_('description de l\'évènement'),
    )

    room = models.ManyToManyField(
        'Room',
        help_text=_('indique dans quelle salle se déroule l\'évènement'),
    )

    start_time = models.DateTimeField(
        help_text=_('début de l\'évènement'),
    )

    end_time = models.DateTimeField(
        help_text=_('fin de l\'évènement'),
    )

    user = models.CharField(
        max_length=50,
        help_text=_('utilisateur ayant fait la demande de réservation'),
    )

    booking_type = models.CharField(
        max_length=50,
        choices=BOOKING_TYPES,
        help_text=_('type d\'évènement'),
    )

    displayable = models.BooleanField(
        help_text=_('affiche ou non cet évènement sur le calendrier'),
        default=True,
    )

    moderated = models.BooleanField(
        help_text=_('indique si l\'évènement a été modéré'),
        default=False,
        editable=False,
    )

    moderated_by = models.CharField(
        max_length=50,
        help_text=_('indique l\'admin qui a modéré l\'évènemnt'),
        default='pas encore modéré',
        editable=False,
    )

    def __str__(self):
        return self.name

    def notify_mailing_list(self):
        user = LdapUser.get(pk=self.user)
        for room in self.room.all():
            if room.location == 'S':
                mail = EmailMessage(
                    subject='Réservation de la salle %s' % room.name,
                    body=('Bonjour,\n\n' +
                          'Ceci est un mail automatique envoyé par le site de réservation de salles du ResEl.\n\n' +
                          'L\'utilisateur %(user)s souhaiterait réserver une salle selon ces informations :\n' +
                          '- salle : %(room)s\n' +
                          '- date de début : %(start_date)s\n' +
                          '- date de fin : %(end_date)s\n\n' +
                          'Vous pouvez contacter cette personne directement en réponse à ce mail.') % {
                                                                                                        'user': user.display_name,
                                                                                                        'room': room.name,
                                                                                                        'start_date': self.start_time,
                                                                                                        'end_date': self.end_time,
                                                                                                        },
                    from_email='noreply@resel.fr',
                    reply_to=[user.mail],
                    to=[room.mailing_list],
                )
                mail.send()

    def notify_moderators(self):
        # TODO
        pass