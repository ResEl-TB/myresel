import base64

from datetime import timedelta
from os import path

import requests
import django_rq

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django_rq import job

@job
def generate_and_email_invoice(user: object, transaction: object, lang: str='fr', send_to:str='user-treasurer') -> None:

    # Get latex invoice
    user['address_formated'] = user['address'].split('\n')

    invoice_latex = render_to_string("tresorerie/invoice.tex", {
        'confLang':lang,
        'transaction': transaction,
        'user': user
    })

    # Send request to laputex
    try:
        laputex_req = requests.post(settings.LAPUTEX_DOC_URL, data={
            'token': settings.LAPUTEX_TOKEN,
            'type': 'latex',
            'content': invoice_latex,
        })
        status_code = laputex_req.status_code
        text = laputex_req.text

    except requests.exceptions.RequestException as err:
        status_code = "'Error handled'"
        text = str(err)


    # Handle response, status_code 201 or 409 means the document is being processed
    if status_code in (201, 409):
        scheduler = django_rq.get_scheduler()

        scheduler.enqueue_in(
            timedelta(seconds=settings.LAPUTEX_WAITING_TIME), invoice_laputex_check,
            user, transaction, laputex_req.json()['UUID'], send_to, 1
        )

    # There is an error, fallback and send error
    else:
        error_display = "New LaPuTeX document request returned {} :\n{}".format(status_code, text)

        queue = django_rq.get_queue()
        queue.enqueue(send_invoice_mail, user, transaction, send_to, errors=error_display)

@job
def invoice_laputex_check(user: object, transaction: object,
                          laputex_invoice_id: str, send_to: str,
                          attempt_num: int=1) -> None:

    # Check LaPuTeX's document's status
    try:
        laputex_req = requests.get(settings.LAPUTEX_DOC_URL + laputex_invoice_id,
                                   data={'token': settings.LAPUTEX_TOKEN})
        no_error = laputex_req.status_code == 200
        status_code = laputex_req.status_code
        text = laputex_req.text

    except requests.exceptions.RequestException as err:
        no_error = False
        status_code = "'Error handled'"
        text = str(err)

    # If it's still compiling, reschedule task
    if no_error and (attempt_num < settings.LAPUTEX_MAX_ATTEMPTS and
                     laputex_req.json()['state'] in ('compiling', 'pending')):
        eta = laputex_req.json()['eta'] if laputex_req.has_key('eta') else settings.LAPUTEX_WAITING_TIME
        scheduler = django_rq.get_scheduler()
        scheduler.enqueue_in(
            timedelta(seconds=eta), invoice_laputex_check,
            user, transaction, laputex_invoice_id, send_to, attempt_num+1
        )

        return

    # Compilation suceeded
    if no_error and laputex_req.json()['state'] == 'ready':
        pdf_raw = laputex_req.json()['document-pdf']
        invoice = base64.b64decode(pdf_raw.encode('utf-8'))
        error_display = ""

    # There is an error, fallback and send error
    else:
        invoice = None
        error_display = "Get LaPuTeX document request returned {} after {} attempts:\n{}"\
                        .format(status_code, attempt_num, text)

    queue = django_rq.get_queue()
    queue.enqueue(
        send_invoice_mail,
        user, transaction, send_to, invoice=invoice, errors=error_display
    )

@job
def send_invoice_mail(user, transaction, send_to, invoice=None, errors=""):
    has_invoice = invoice != None

    # Mail for user
    if 'user' in send_to:
        # Render the mail from template
        content = render_to_string(
            "tresorerie/mails/invoice_to_user.txt",
            {'transaction': transaction, 'user': user, 'has_invoice': has_invoice}
        )

        # User should receive a mail from treasurer but reply-to support
        mail_for_user = EmailMessage(
            subject=_("Facture ResEl"),
            body=content,
            from_email=settings.TREASURER_EMAIL,
            to=[user['email']],
            reply_to=[settings.SUPPORT_EMAIL],
        )

        # Attach the invoice if there is one before sending
        if has_invoice:
            mail_for_user.attach(user['uid']+'.pdf', invoice, 'application/pdf')

        mail_for_user.send()

    # Mail for treasurer
    if 'treasurer' in send_to:
        content = render_to_string(
            "tresorerie/mails/invoice_to_treasurer.txt",
            {'transaction': transaction, 'user': user, 'has_invoice': has_invoice, 'errors': errors}
        )

        # Treasurer should receive mail from server
        mail_for_treasurer = EmailMessage(
            subject=_("Facture ResEl") + " " + str(user['uid']),
            body=content,
            from_email=settings.SERVER_EMAIL,
            to=[settings.TREASURER_EMAIL]
        )

        # Save invoice persistently in admin site then attach it to the mail
        if has_invoice:
            dest = path.join(settings.PROJECT_ROOT, settings.INVOICE_STORE_PATH,
                             user['uid'] + '-' + str(transaction['uuid']) + '.pdf')
            with open(dest, 'wb') as pdf_file:
                pdf_file.write(invoice)

            mail_for_treasurer.attach(user['uid']+'.pdf', invoice, 'application/pdf')

        mail_for_treasurer.send()

    if not 'treasurer' in send_to and not 'user' in send_to:
        raise ValueError("send_to parameter should contain 'treasurer' or/and 'user', got '{}'".format(send_to))

#### OLD
# @job
# def generate_and_email_invoice(user, transaction, lang='fr'):

#     # Get the user in LDAP for it's address
#     from gestion_personnes.models import LdapUser
#     user_l = LdapUser.get(uid=user.uid)
#     user.address_first, user.address_second = user_l.postal_address.split('\n')

#     # Args for compilation
#     generation_args = {
#         'confLang': lang,
#         'transaction': transaction,
#         'user': user,
#     }

#     filename = 'facture-{}-{}'.format(user.uid, str(transaction.uuid)[:8])
#     # Generating french invoice
#     invoice_path_fr = generate_pdf(
#         'tresorerie/facture.tex',
#         generation_args,
#         filename,
#         settings.INVOICE_STORE_PATH
#     )

#     # Save it in DB
#     transaction.facture = "invoices/" + filename + ".pdf"
#     transaction.save()
#     main_product = transaction.get_main_product()
#     if main_product.type_produit == "A":
#         mail_message = ("Bonjour %s,\n\n" +
#                         "Nous vous confirmons que nous avons bien reçu le paiement de votre cotisation pour l'année %s !\n" +
#                         "Votre facture se trouve en pièce jointe de cet email.\n\n" +
#                         "Vous pouvez l'enregistrer, mais si vous la perdez, vous pourrez toujours la télécharger depuis la page \"Historique de mes factures\" sur le site du ResEl.\n" +
#                         "Vous êtes désormais pleinement membre de l'association et profitez de ses services internes : IPTV, sites des clubs, campus et bien plus.\n\n" +
#                         "Si vous souhaitez accéder à Internet, il vous faut payer vos frais via le site du ResEl.\n\n" +
#                         "L'équipe d'administrateurs reste à votre disposition pour toute question ou tout problème.\n\n" +
#                         "Cordialement,\n\n" +
#                         "L'équipe du ResEl.") % (user.first_name, current_year())

#     elif main_product.type_produit == "F":
#         mail_message = ("Bonjour %s,\n\n" +
#                         "Nous vous confirmons que nous avons bien reçu le paiement de vos frais d'accès à Internet !\n" +
#                         "Votre facture se trouve en pièce jointe de cet email.\n" +
#                         "Vous pouvez l'enregistrer, mais si vous la perdez, vous pourrez toujours la télécharger depuis la page \"Historique de mes factures\" sur le site du ResEl.\n" +
#                         "Vous y trouverez aussi la date de fin de votre accès à Internet.\n\n" +
#                         "En cas de problème de tout type avec votre connexion, n'ayez aucune hésitation à contacter l'équipe d'administrateurs par email à support@resel.fr / support-rennes@resel.fr. " +
#                         "Vous pouvez aussi venir directement nous voir aux permanences qui se tiennent tous les jours de semaine de 18h à 19h30 au foyer des élèves.\n" +
#                         "Nous ferons tout notre possible pour résoudre votre problème. " +
#                         "Cordialement,\n\n" +
#                         "L'équipe du ResEl.") % (user.first_name)
#     elif main_product.type_produit == "M":
#         mail_message = ("Bonjour %s,\n\n" +
#                         "Nous vous confirmons que nous avons bien reçu le paiement pour le matériel (câble, switch ...) que vous venez d'acquérir.\n" +
#                         "Votre facture se trouve en pièce jointe de cet email.\n\n" +
#                         "Vous pouvez l'enregistrer, mais si vous la perdez, vous pourrez toujours la télécharger depuis la page \"Historique de mes factures\" sur le site du ResEl.\n" +
#                         "N'hésitez pas à revenir nous voir si vous rencontrez un problème avec votre matériel.\n\n" +
#                         "Cordialement,\n\n" +
#                         "L'équipe du ResEl.") % (user.first_name)

#     # Send it by email
#     user_email = EmailMessage(
#         subject=_("Facture ResEl"),
#         body=mail_message,
#         from_email="tresorier@resel.fr",
#         reply_to=["support@resel.fr"],
#         to=[user.mail],
#     )

#     treasurer_email = EmailMessage(
#         subject="Facture ResEl " + str(user.uid),
#         body="""%s vient d'effectuer un paiement de %f €.\nVeuillez trouver ci-joint la facture."""
#              % (user.uid, transaction.total),
#         from_email=SERVER_EMAIL,
#         to=["tresorier@resel.fr"],
#     )

#     with open(invoice_path_fr, 'rb') as file:
#         user_email.attach(filename + ".pdf", file.read(), "application/pdf")
#     with open(invoice_path_fr, 'rb') as file:
#         treasurer_email.attach(filename + ".pdf", file.read(), "application/pdf")

#     treasurer_email.send()
#     user_email.send()

