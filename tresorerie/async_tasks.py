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
        laputex_req = requests.post(settings.LAPUTEX_DOC_URL,
                                    headers={'token': settings.LAPUTEX_TOKEN},
                                    data={'type': 'latex', 'content': invoice_latex})
        status_code = laputex_req.status_code
        text = laputex_req.text

    except requests.exceptions.RequestException as err:
        print(err)
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
                                   headers={'token': settings.LAPUTEX_TOKEN})
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

        # Save invoice persistently in admin site then attach it to the mail
        if has_invoice:
            dest = path.join(settings.MEDIA_ROOT, settings.INVOICE_STORE_PATH,
                             user['uid'] + '-' + str(transaction['uuid']) + '.pdf')
            with open(dest, 'wb') as pdf_file:
                pdf_file.write(invoice)

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

        # Attach the invoice if there is one before sending
        if has_invoice:
            mail_for_treasurer.attach(user['uid']+'.pdf', invoice, 'application/pdf')

        mail_for_treasurer.send()

    if not 'treasurer' in send_to and not 'user' in send_to:
        raise ValueError("send_to parameter should contain 'treasurer' or/and 'user', got '{}'".format(send_to))
