from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django_rq import job

from fonctions.latexWrapper import generate_pdf
from gestion_personnes.models import LdapUser
from myresel.settings import SERVER_EMAIL


@job
def generate_and_email_invoice(user, transaction, lang='fr'):

    # Get the user in LDAP for it's address
    user_l = LdapUser.get(uid=user.uid)
    user.address_first, user.address_second = user_l.postal_address.split('\n')

    # TODO : add functionnality to invoice misc thing such as cable, router, etc...

    # Args for compilation
    generation_args = {
        'confLang': lang,
        'transaction': transaction,
        'user': user,
    }

    filename = 'facture-{}-{}'.format(transaction.pk, user.uid)
    # Generating french invoice
    invoice_path_fr = generate_pdf(
        'tresorerie/facture.tex',
        generation_args,
        filename,
        settings.INVOICE_STORE_PATH
    )
    # Generating invoice in user lang if different
    if lang != 'fr':
        generation_args['confLang'] = lang
        invoice_path_en = generate_pdf(
            'tresorerie/facture.tex',
            generation_args,
            filename,
            settings.INVOICE_STORE_PATH
        )

    # Save it in DB
    transaction.facture = filename

    # Send it by email
    user_email = EmailMessage(
        subject=_("Facture ResEl"),
        body="Bonjour " + str(user.first_name) +
        "\nVous recevez cet email pour vous confirmer le paiement de vos frais d'accès à internet." +
        "\nVeuillez trouver ci-joint la facture de votre paiement" +
        "\n\nHello " + str(user.first_name) +
        "\nYou receive this mail to confirm you the payment of you internet access fees." +
        "\nYou will find your invoice enclosed in this email.",
        from_email="tresorier@resel.fr",
        reply_to=["support@resel.fr"],
        to=[user.mail],
    )
    if lang != 'fr':
        with open(invoice_path_en, 'rb') as file:
            user_email.attach(filename, file.read())
    else:
        with open(invoice_path_fr, 'rb') as file:
            user_email.attach(filename, file.read())

    treasurer_email = EmailMessage(
        subject="Facture ResEl " + str(user.first_name),
        body= str(user.first_name) + " vient d'effectuer un paiement." +
        "\nVeuillez trouver ci-joint la facture.",
        from_email=SERVER_EMAIL,
        to=["tresorier@resel.fr"],
    )
    with open(invoice_path_fr, 'rb') as file:
        user_email.attach(filename, file.read())
        treasurer_email.attach(filename, file.read())

    treasurer_email.send()
    user_email.send()
