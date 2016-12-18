# -*- coding: utf-8 -*-
"""
This file combine every async tasks that are used during a user management
The backend used to manage the async queue is redis with the plugins rq & django-rq
redis : http://redis.io/
rq : http://python-rq.org/
django-rq : https://github.com/ui/django-rq
"""
from django.core.mail import EmailMessage, mail_admins
from django.utils.translation import ugettext as _
from django_rq import job

from myresel import settings


@job
def send_mails(user) -> None:
    """
    Send emails to the spectified user when he creates an account
     - Subscribe him to campus email
     - Welcoming e-mail
     - email for admins
    """
    # Subscribe to campus@resel.fr
    campus_email = EmailMessage(
        subject="SUBSCRIBE campus {} {}".format(user.first_name,
                                                user.last_name),
        body="Inscription automatique de {} a campus".format(user.uid),
        from_email=user.mail,
        reply_to=["listmaster@resel.fr"],
        to=["sympa@resel.fr"],
    )

    # Send a validation email to the user
    # TODO: rédiger un peu plus ce mail et le faire valider par le respons' com
    # TODO: ajouter un email pour faire valider l'adresse email
    user_email = EmailMessage(
        subject=_("Inscription au ResEl"),
        body="Bonjour," +
             "\nVous êtes désormais inscrit au ResEl, voici vos identifiants :" +
             "\nNom d'utilisateur : " + str(user.uid) +
             "\nMot de passe : **** (celui que vous avez choisi lors de l'inscription)" +

             "\n\n Vous pouvez, si vous souhaitez, changer votre mot de passe (en suivant ce lien https://my.resel.fr/personnes/modification-passwd)" +
             "\n Ainsi que tout les paramètres de votre compte." +

             "\n\n En étant membre de l'association ResEl vous pouvez profiter de ses nombreux services et des "
             "activités que l'association propose." +
             "\n N'hésitez pas à naviguer sur notre site (https://resel.fr) pour y découvrir tout ce que nous proposons." +

             "\n\nPour avoir accès à internet, vous allez devoir inscrire chacune de vos machines (ordinateurs, smartphones, etc...) à notre réseau." +
             "\nRendez vous sur notre site web, vous serez guidé à travers cette dernière étape." +

             "\n\nSi vous avez le moindre problème, la moindre question, la moindre envie de nous féliciter, ou de nous faire des bisous baveux," +
             "vous pouvez répondre à cet e-mail, ou venir nous voir pendant nos permanences, celles-ci ont lieu tous les jours en semaine de 18h à 19h30" +
             "au foyer des élèves de Télécom Bretagne." +

             "\n\nSi vous êtes intéressé pour nous aider, pour travailler avec nous au sein de l'association, pour mettre à disposition vos compétences," +
             "ou même si vous n'avez pas de compétences mais que vous souhaitez apprendre, vous pouvez aussi nous contacter pour faire partie de l'équipe" +
             " d'administrateurs !" +

             "\n\nÀ bientôt, l'équipe ResEl.",
        from_email="inscription@resel.fr",
        to=[user.mail],
    )

    mail_admins("Inscription de %s" % str(user.uid),
                "Nouvel inscrit au ResEl par le site web :"
                "\n\nuid : %(username)s"
                "\nNom : %(lastname)s"
                "\nPrénom : %(firstname)s"
                "\nemail : %(mail)s"
                "\nCampus : %(campus)s"
                "\n\n Ce mail est un mail automatique envoyé par l'interface d'inscription du ResEl. " % {
                    "username": user.uid,
                    "lastname": user.last_name,
                    "firstname": user.first_name,
                    "mail": user.mail,
                    "campus": settings.CURRENT_CAMPUS
                })

    campus_email.send()
    user_email.send()
