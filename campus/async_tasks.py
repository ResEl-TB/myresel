from django_rq import job

@job
def notify_mailing_list(user, room):
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