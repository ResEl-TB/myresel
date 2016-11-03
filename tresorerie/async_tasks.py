from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django_rq import job

from fonctions.generic import current_year
from fonctions.latexWrapper import generate_pdf
from gestion_personnes.models import LdapUser
from myresel.settings import SERVER_EMAIL


@job
def generate_and_email_invoice(user, transaction, lang='fr'):

    # Get the user in LDAP for it's address
    user_l = LdapUser.get(uid=user.uid)
    user.address_first, user.address_second = user_l.postal_address.split('\n')

    # Args for compilation
    generation_args = {
        'confLang': lang,
        'transaction': transaction,
        'user': user,
    }

    filename = 'facture-{}-{}'.format(user.uid, str(transaction.uuid)[:8])
    # Generating french invoice
    invoice_path_fr = generate_pdf(
        'tresorerie/facture.tex',
        generation_args,
        filename,
        settings.INVOICE_STORE_PATH
    )

    # Save it in DB
    transaction.facture = "invoices/" + filename + ".pdf"
    transaction.save()
    main_product = transaction.get_main_product()
    if main_product.type_produit == "A":
        mail_message = ("Bonjour %s,\n\n" +
                        "Nous vous confirmons que nous avons bien reçu le paiement de votre cotisation pour l'année %s !\n" +
                        "Votre facture se trouve en pièce jointe de cet email.\n\n" +
                        "Vous pouvez l'enregistrer, mais si vous la perdez, vous pourrez toujours la télécharger depuis la page \"Historique de mes factures\" sur le site du ResEl.\n" +
                        "Vous êtes désormais pleinement membre de l'association et profitez de ses services internes : IPTV, sites des clubs, campus et bien plus.\n\n" +
                        "Si vous souhaitez accéder à Internet, il vous faut payer vos frais via le site du ResEl.\n\n" +
                        "L'équipe d'administrateurs reste à votre disposition pour toute question ou tout problème.\n\n" +
                        "Cordialement,\n\n" +
                        "L'équipe du ResEl.") % (user.first_name, current_year())

    elif main_product.type_produit == "F":
        mail_message = ("Bonjour %s,\n\n" +
                        "Nous vous confirmons que nous avons bien reçu le paiement de vos frais d'accès à Internet !\n" +
                        "Votre facture se trouve en pièce jointe de cet email.\n" +
                        "Vous pouvez l'enregistrer, mais si vous la perdez, vous pourrez toujours la télécharger depuis la page \"Historique de mes factures\" sur le site du ResEl.\n" +
                        "Vous y trouverez aussi la date de fin de votre accès à Internet.\n\n" +
                        "En cas de problème de tout type avec votre connexion, n'ayez aucune hésitation à contacter l'équipe d'administrateurs par email à support@resel.fr / support-rennes@resel.fr. " +
                        "Vous pouvez aussi venir directement nous voir aux permanences qui se tiennent tous les jours de semaine de 18h à 19h30 au foyer des élèves.\n" +
                        "Nous ferons tout notre possible pour résoudre votre problème. " +
                        "Cordialement,\n\n" +
                        "L'équipe du ResEl.") % (user.first_name)
    elif main_product.type_produit == "M":
        mail_message = ("Bonjour %s,\n\n" +
                        "Nous vous confirmons que nous avons bien reçu le paiement pour le matériel (câble, switch ...) que vous venez d'acquérir.\n" +
                        "Votre facture se trouve en pièce jointe de cet email.\n\n" +
                        "Vous pouvez l'enregistrer, mais si vous la perdez, vous pourrez toujours la télécharger depuis la page \"Historique de mes factures\" sur le site du ResEl.\n" +
                        "N'hésitez pas à revenir nous voir si vous rencontrez un problème avec votre matériel.\n\n" +
                        "Cordialement,\n\n" +
                        "L'équipe du ResEl.") % (user.first_name)

    # Send it by email
    user_email = EmailMessage(
        subject=_("Facture ResEl"),
        body=mail_message,
        from_email="tresorier@resel.fr",
        reply_to=["support@resel.fr"],
        to=[user.mail],
    )

    treasurer_email = EmailMessage(
        subject="Facture ResEl " + str(user.uid),
        body="""%s vient d'effectuer un paiement de %f €.\nVeuillez trouver ci-joint la facture."""
             % (user.uid, transaction.total),
        from_email=SERVER_EMAIL,
        to=["tresorier@resel.fr"],
    )

    with open(invoice_path_fr, 'rb') as file:
        user_email.attach(filename + ".pdf", file.read(), "application/pdf")
    with open(invoice_path_fr, 'rb') as file:
        treasurer_email.attach(filename + ".pdf", file.read(), "application/pdf")

    treasurer_email.send()
    user_email.send()
