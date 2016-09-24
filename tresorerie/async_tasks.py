from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django_rq import job

from fonctions.latexWrapper import generate_pdf
from gestion_personnes.models import LdapUser
from myresel.settings import SERVER_EMAIL


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
    user_email = EmailMessage(
        subject=_("Facture ResEl"),
        body="Bonjour " + str(user.first_name) +
        "\nVous recevez cet email pour vous confirmer le paiement de vos frais d'accès à internet." +
        "\nVeuillez trouver ci-joint la facture de votre paiement" +
        "\n\nHello " + str(user.first_name) +
        "\nYou receive this mail to confirm you the payment of you internet access fees." +
        "\nYou will find your invoice enclosed in this email.",
        from_email=SERVER_EMAIL,
        reply_to=["support@resel.fr"],
        to=[user.mail],
    )
    if lang != 'fr':
        with open(invoice_path_en, 'rb') as file:
            user_email.attach('facture-{}-{}-{}'.format(invoice.pk, user.username, lang), file.read())
    else :
        with open(invoice_path_fr, 'rb') as file:
            user_email.attach('facture-{}-{}-{}'.format(invoice.pk, user.username, lang), file.read())

    treasurer_email = EmailMessage(
        subject="Facture ResEl " + str(user.first_name),
        body= str(user.first_name) + " vient d'effectuer un paiement." +
        "\nVeuillez trouver ci-joint la facture.",
        from_email=SERVER_EMAIL,
        to=["tresorier@resel.fr"],
    )
    with open(invoice_path_fr, 'rb') as file:
        user_email.attach('facture-{}-{}-{}'.format(invoice.pk, user.username, lang), file.read())


    try:
        treasurer_email.send()
        user_email.send()
    except Exception:
        pass