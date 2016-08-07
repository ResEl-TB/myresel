from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_rq import job

from fonctions.latexWrapper import generate_pdf 

@job
def generate_and_email_invoice(user, price, invoice, lang='fr'):
    
    # Formatting address
    user_address_first = 'Bâtiment {}, Chambre {} - Maisel Télécom Bretagne'.format(user.batiment, user.roomNumber)
    if user.campus == "rennes":
        user_address_second = '2, rue de la Châtaigneraie - 35576 - Cesson Sévigné'
    else: # If we don't know, we suppose it's Brest
        user_address_second = '655 avenue du Technopôle - 29280 - Plouzané'

    invoice_categories = []

    # Check if he paid the cotisation
    if price in [1100, 1770, 2940, 5100, 8600]:
        invoice_categories.append(
            {
                'name': _('Cotisation'),
                'products': [{'quantity': 1, 'name': "Cotisation d'un an à l'association", 'price': 1},]
            },
        )

    invoice_categories.append(
        {
            'name': _('Internet'),
            'products': [{'quantity': 1, 'name': invoice.comment, 'price': invoice.total},]
        },
    )

    # TODO : add functionnality to invoice misc thing such as cable, router, etc...
#    {
#        'name': _('Divers'),
#        'products': [[1, pt.ethernetCable3m], [1, pt.router],]
#    },

    # Args for compilation
    generation_args = {
        'confLang': lang, 
        'user': {
            'uid': user.uid,
            'firstName': user.firstname,
            'lastName': user.lastname,
            'addressFirstPart': user_address_first,
            'addressSecondPart': user_address_second,
        },
        'invoice': {
            'id': invoice.pk,
            'date': '\\today',
            'categories': invoice_categories,
            'payment': {
                'isPaid': True,
                'date': invoice.date,
                'info': invoice.moyen,
            }
        }
    }

    # Generating invoice
    invoice_path_fr = generate_pdf(
        'tresorerie/facture.tex',
        generation_args,
        'facture-{}-{}'.format(user.uid, invoice.pk),
        settings.INVOICE_STORE_PATH
    )
    if lang != 'fr':
        invoice_path_en = generate_pdf(
            'tresorerie/facture.tex',
            generation_args,
            'facture-{}-{}-en'.format(user.uid, invoice.pk),
            settings.INVOICE_STORE_PATH
        )

    # Save it in DB
    # TODO

    # Send it by email
    # TODO :
    # if lang != 'fr':
    # send email with english invoice
    # send email to tresorier@resel.fr with french invoice
