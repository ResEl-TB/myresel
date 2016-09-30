import os
from uuid import UUID

from django.core import mail
from django.test import TestCase

from gestion_personnes.tests import try_delete_user, create_full_user
from myresel import settings
from tresorerie.async_tasks import generate_and_email_invoice
from tresorerie.models import Transaction, Product


class InvoiceCreation(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)
        self.user.save()

        self.productFIG_1m = Product(
            nom="1 mois ResEl",
            prix=1000,
            type_produit="F",
            duree=1,
            autorisation="ALL",
        )

        self.productAdhesion = Product(
            nom="Adhesion au ResEl",
            prix=100,
            type_produit="A",
            duree=12,
            autorisation="ALL",
        )
        self.productFIG_1m.save()
        self.productAdhesion.save()

        self.transaction = Transaction()
        self.transaction.utilisateur = self.user.uid
        self.transaction.moyen = "CB"
        self.transaction.save()

        self.transaction.produit.add(self.productAdhesion)
        self.transaction.produit.add(self.productFIG_1m)
        self.transaction.save()

    def test_simple_invoice(self):
        self.transaction.uuid=UUID("dfa23979-e9f5-4297-93bd-520f00439faa")

        generate_and_email_invoice(self.user, self.transaction)

        # Open a file
        with open(os.path.join(settings.INVOICE_STORE_PATH,
                               "facture-{}-{}.pdf".format(self.transaction.pk, self.user.uid))):
            pass

        self.assertEqual(2, len(mail.outbox))


class test_product(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)
        self.user.save()

        self.productFIG_1m = Product(
            nom="1 mois ResEl",
            prix=1000,
            type_produit="F",
            duree=1,
            autorisation="ALL",
        )

        self.productAdhesion = Product(
            nom="Adhesion au ResEl",
            prix=100,
            type_produit="A",
            duree=12,
            autorisation="ALL",
        )
        self.productFIG_1m.save()
        self.productAdhesion.save()

    def test_get_main_product_simple(self):

        self.transaction = Transaction()
        self.transaction.utilisateur = self.user.uid
        self.transaction.moyen = "CB"
        self.transaction.save()

        self.transaction.produit.add(self.productAdhesion)
        self.transaction.produit.add(self.productFIG_1m)
        self.transaction.save()

        transaction_s = Transaction.objects.get(pk=self.transaction.pk)
        main_product = transaction_s.get_main_product()
        self.assertEqual(main_product.nom, self.productFIG_1m.nom)