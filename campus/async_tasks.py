# -*- coding: utf-8 -*-
"""
Declare all the async jobs for the campus module
"""
from django.core.mail import EmailMessage
from django.urls import reverse

from django_rq import job

@job
def notify_mailing_list(user, room):
    """
    Notify a club mailing list that a room is reserved
    :param user:
    :param room:
    :return:
    """
    # TODO: add reservation start and end
    mail = EmailMessage(
        subject='Réservation de la salle %s' % room.name,
        body=(
                 'Bonjour,\n\n' +
                 'Ceci est un mail automatique envoyé par le site de réservation de salles du ResEl.\n\n' +
                 'L\'utilisateur %(user)s souhaiterait réserver une salle selon ces informations :\n' +
                 '- salle : %(room)s\n' +
                 # '- date de début : %(start_date)s\n' +
                 #  '- date de fin : %(end_date)s\n\n' +
                 'Vous pouvez contacter cette personne directement en réponse à ce mail.') % {
                    'user': user.display_name,
                    'room': room.name,
                    # 'start_date': self.start_time,
                    # 'end_date': self.end_time,
                },
        from_email='secretaire@resel.fr',
        reply_to=[user.mail],
        to=[room.mailing_list],
    )
    mail.send()

@job
def notify_moderator(moderator_address, mail_id, sender, subject, content):
    """
    Notify the campus moderators that an email has arrived
    :param moderator_address:
    :param mail_id:
    :param content: content of the mail
    :return:
    """
    # TODO: create direct validate link
    mail = EmailMessage(
        subject='Mail campus à modérer: "%s"' % subject,
        body=('Bonjour,\n\n' +
              'Un nouveau mail campus requiert votre modération.\n' +
              'Vous pouvez suivre ce lien pour le faire :\n' +
              'https://resel.fr' + reverse("campus:mails:moderate") + '\n\n' +
              '---------- aperçu ----------\n\n' +
              'De : ' + sender +
              '\n' +
              'Sujet : ' + subject +
              '\n\n' +
              content +
              '\n\n' +
              '----------------------------\n\n' +
              'Pour toute demande annexe : ' +
              'support@resel.fr ou https://resel.fr/support\n\n' +
              'Have fun,\n' +
              '~ Le gentil bot ResEl ~'
        ),
        from_email='secretaire@resel.fr',
        to=[moderator_address],
    )
    mail.send()
