from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_rq import job

from fonctions import ldap
from fonctions.latexWrapper import generate_pdf 

@job
def generate_and_email_invoice(user, price, invoice, lang='fr'):

    # Get the user in LDAP for it's address
    try:
        user_l = LdapUser.objects.get(uid=user.username)
        if user_l.batiment != "":
            user_address_first = 'Bâtiment {}, Chambre {} - Maisel Télécom Bretagne'.format(user_l.batiment, user_l.roomNumber)
            if user_l.campus == "rennes":
                user_address_second = '2, rue de la Châtaigneraie - 35576 - Cesson Sévigné'
            else: # If we don't know, we suppose it's Brest
                user_address_second = '655 avenue du Technopôle - 29280 - Plouzané'
        elif user_l.postalAddres != "":
            user_address_first = user_l.postalAddres
            user_address_second = ''    
        else :
            user_address_first = ''
            user_address_second = ''
    except:
        user_address_first = 'Maisel Télécom Bretagne'
        user_address_second = '655 avenue du Technopôle - 29280 - Plouzané'

    invoice_categories = []

    # Check if he paid the cotisation
    if price in [1100, 1770, 2940, 5100, 8600]:
        invoice_categories.append(
            {
                'name': _('Cotisation'),
                'products': [{'quantity': 1, 'name': _("Adhésion à l'Association"), 'price': 1},]
            },
        )

    invoice_categories.append(
        {
            'name': _('Internet'),
            'products': [{'quantity': 1, 'name': invoice.commentaire, 'price': invoice.total},]
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
            'uid': user.username,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'addressFirstPart': user_address_first,
            'addressSecondPart': user_address_second,
        },
        'invoice': {
            'id': invoice.pk,
            'date': invoice.date,
            'categories': invoice_categories,
            'payment': {
                'isPaid': True,
                'date': invoice.date,
                'info': invoice.moyen,
            }
        }
    }

    # Generating french invoice
    generation_args['confLang'] = 'fr'
    invoice_path_fr = generate_pdf(
        'tresorerie/facture.tex',
        generation_args,
        'facture-{}-{}'.format(invoice.pk, user.username),
        settings.INVOICE_STORE_PATH
    )
    # Generating invoice in user lang if different
    if lang != 'fr':
        generation_args['confLang'] = lang
        invoice_path_en = generate_pdf(
            'tresorerie/facture.tex',
            generation_args,
            'facture-{}-{}-{}'.format(invoice.pk, user.username, lang),
            settings.INVOICE_STORE_PATH
        )

    # Save it in DB
    # TODO

    # Send it by email
    # TODO :
    # if lang != 'fr':
    # send email with english invoice
    # send email to tresorier@resel.fr with french invoice
