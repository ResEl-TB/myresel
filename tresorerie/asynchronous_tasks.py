from django.conf import settings
from django.utils import timezone
from django_rq import job

from fonctions.latexWrapper import generate_pdf 

#@job
def generate_and_email_invoice(user, invoice, lang='fr'):
    
    # Formatting address
    user_address_first = 'Bâtiment {}, Chambre {} - Maisel Télécom Bretagne'.format(user.batiment, user.roomNumber)
    if user.campus == "rennes":
        user_address_second = '2, rue de la Châtaigneraie - 35576 - Cesson Sévigné'
    else: # If we don't know, we suppose it's Brest
        user_address_second = '655 avenue du Technopôle - 29280 - Plouzané'

    # Args for compilation
    generation_args = {
        'confLang': lang, 
        'user': {
            'uid': user.uid,
            'firstName': user.firstname,
            'lastName': user.lastname,
            'addressFirstPart': "",
            'addressSecondPart': "",
        },
        'invoice': {
            'id': invoice.pk,
            'date': '\\today',
            'internetFeesPrice': invoice.total,
            'isPaid': 'yes',
            'payment': {
                'date': invoice.date,
                'info': invoice.moyen,
            }
        }
    }

    # Generating invoice
    invoice_path_fr = generate_pdf(
        'tresorerie/facture.tex',
        generation_args,
        'facture-{}-{}'.format(user.uid, invoice.id),
        settings.INVOICE_STORE_PATH
    )
    if lang != 'fr':
        invoice_path_en = generate_pdf(
            'tresorerie/facture.tex',
            generation_args,
            'facture-{}-{}-en'.format(user.uid, invoice.id),
            settings.INVOICE_STORE_PATH
        )

    # Save it in DB
    # TODO

    # Send it by email
    # TODO :
    # if lang != 'fr':
    # send email with english invoice
    # send email to tresorier@resel.fr with french invoice
