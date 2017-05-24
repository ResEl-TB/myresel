import os
import time

import uuid

import django_rq

from django.core import mail
from django.test import TestCase

from gestion_personnes.tests import try_delete_user, create_full_user
from myresel import settings
from tresorerie.async_tasks import generate_and_email_invoice
from tresorerie.models import Transaction, Product

import logging

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
        self.transaction.uuid = uuid.uuid4()

        # Gather information and launch tasks for sending invoice
        user_datas = {
            'first_name': self.user.first_name,
            'last_name' : self.user.last_name,
            'uid': self.user.uid,
            'email' : self.user.mail,
            'address' : self.user.postal_address,
        }
        transaction_datas = {
            'uuid': self.transaction.uuid,
            'date_creation': self.transaction.date_creation,
            'date_paiement': self.transaction.date_creation,
            'statut': self.transaction.statut,
            'moyen': self.transaction.get_moyen_display(),
            'total': self.transaction.total,
            'admin': self.transaction.admin,
            'categories': [
                {'name': cat, 'products': prods} for cat, prods in self.transaction.get_products_by_cat()
            ],
        }

        django_rq.get_worker().work(burst=True)
        queue = django_rq.get_queue()
        scheduler = django_rq.get_scheduler()

        queue.enqueue_call(
            generate_and_email_invoice,
            args=(user_datas, transaction_datas, 'fr', 'user-treasurer'),
        )

        # Wait all tasks are done
        time_begin = time.time()
        while len(scheduler.get_jobs()) > 0 or len(queue.get_jobs()) > 0:
            if time.time() - time_begin > 120:
                raise ValueError("Waited too long")
            time.sleep(4)


        # Check
        filename = os.path.join(settings.MEDIA_ROOT, settings.INVOICE_STORE_PATH,
                                "{}-{}.pdf".format(self.user.uid, str(self.transaction.uuid)))

        self.assertTrue(os.path.isfile(filename))

        # This assert doesn't work because mail sending is done in another process
        # and django's mail.outbox isn't updated;
        # TODO : Found a solution !
        #self.assertEqual(2, len(mail.outbox))


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
