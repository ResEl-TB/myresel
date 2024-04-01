from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from tresorerie.models import MonthlyPayment, Transaction
from datetime import date, timedelta
from fonctions import ldap
import stripe

class Command(BaseCommand):
    help = "Vérifie les paiements mensualisés, et facture l'utilisateur s'il le faut"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_API_KEY

        for payment in MonthlyPayment.objects.all():
            if payment.last_paid + timedelta(days=30) <= date.today():
                user = ldap.search(settings.LDAP_DN_PEOPLE, '(&(uid=%s))' % payment.user, ['mail'])[0]
                try:
                    stripe.Charge.create(amount=int(payment.amount_to_pay*100), currency="eur", customer=payment.customer)
                    payment.months_paid += 1
                    payment.save()

                    Transaction.objects.create(
                        utilisateur=payment.user,
                        total=payment.amount_to_pay,
                        commentaire=_("Accès Internet - %se mensualisation" % payment.months_paid)
                    )

                    mail = EmailMessage(
                        subject=_("Notification de paiement de mensualité"),
                        body=_(
                            "Bonjour %s,\n\n" % payment.user +

                            "Nous vous informons que le paiement de votre %se mensualité vient d'être accepté. Si vous recevez ce mail" +
                            " par erreur, nous vous invitons à nous contacter urgemment afin d'en déterminer la cause et de procéder" +
                            " aux ajustements nécessaires.\n\n" % payment.months_paid +

                            "Nous restons à votre disposition si vous avez la moindre question à support@resel.fr\n\n" +

                            "Cordialement,\n" +
                            "le Trésorier ResEl"
                            ),
                        from_email='tresorier@resel.fr',
                        reply_to=['tresorier@resel.fr'],
                        to=[user.mail[0]],
                    )
                    mail.send()

                    if payment.months_paid >= payment.months_to_pay:
                        payment.delete()

                except stripe.error.CardError as e:
                    code = e.json_body['error']['code']

                    ERRORS = {
                        'expired_card': _("Votre carte a expiré"),
                        'card_declined': _("Votre carte a été refusée"),
                        'processing_error': _("Une erreur est survenue dans le traitement de votre demande")
                    }

                    mail = EmailMessage(
                        subject="[Resel.fr] Erreur dans le paiement d'une mensualité",
                        body="Hello bitches,\n\n" +

                            "Une erreur est survenue dans la tentative de facturation de la %de mensualité" % (payment.months_paid + 1) +
                            " de l'utilisateur %s. Il a été prévenu, et vous l'êtes aussi. Prenez contact avec lui," % payment.user +
                            " histoire de régler ça rapidement.\n\n" +

                            "L'erreur est la suivante : '%s'\n\n" % ERRORS[code] +

                            "Ce mail a été envoyé automatiquement suite au lancement de la commande" +
                            " '/srv/www/resel.fr/manage.py check-payments'",
                        from_email='treso-bot@resel.fr',
                        to=['tresorier@resel.fr'],
                    )
                    mail.send()

                    mail = EmailMessage(
                        subject=_("Notification de paiement de mensualité"),
                        body=_(
                            "Bonjour %s,\n\n" % payment.user +

                            "Nous vous informons que le paiement de votre %de mensualité vient d'être refusé." % (payment.months_paid + 1) +
                            "Les administrateurs ont été prévenus, vous recevrez un message de leur part d'ici peu" +
                            " de temps afin de clarifier et de régler ce problème.\n\n" +

                            "Nous restons à votre disposition si vous avez la moindre question à support@resel.fr\n\n" +

                            "Cordialement,\n" +
                            "le Trésorier ResEl"
                            ),
                        from_email='tresorier@resel.fr',
                        reply_to=['tresorier@resel.fr'],
                        to=[user.mail[0]],
                    )
                    mail.send()

                except stripe.error.RateLimitError as e:
                    pass

                except stripe.error.APIConnectionError as e:
                    pass
