# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase

from fonctions.generic import current_year
from gestion_personnes.models import LdapUser
from gestion_personnes.tests import create_full_user, try_delete_user
from myresel import settings
from tresorerie.models import Transaction, Product

import stripe


class HistoryViewCase(TestCase):

    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)
        self.user.save()
        self.client.login(username=self.user.uid, password=self.user.user_password)

    def test_no_transactions(self):
        r = self.client.get(reverse("tresorerie:historique"),
                                   HTTP_HOST="10.0.3.94", follow=True)
        self.assertContains(r, "Pas de paiements trouvés dans la base de données.")
        self.assertTemplateUsed(r, "tresorerie/history.html")

    def test_some_transactions(self):
        # Add some transactions
        transactions_values = [20, 25, 12, 81, 87, 12]
        for p in transactions_values:
            t = Transaction()
            t.utilisateur = self.user.uid
            t.total = p
            t.save()

        r = self.client.get(reverse("tresorerie:historique"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertNotContains(r, "Pas de paiements trouvés dans la base de données.")
        self.assertTemplateUsed(r, "tresorerie/history.html")
        for p in transactions_values:
            self.assertContains(r, str(p))

class HomeViewCaseMeta(type):
    def __new__(mcs, name, bases, attrs):
        """
        For generating arbitrary test cases
        https://chris-lamb.co.uk/posts/generating-dynamic-python-tests-using-metaclasses
        """
        for f in ('FIP', 'FIG', 'ANY'):
            attrs['test_product_display_%s' % f.lower()] = mcs.product_display_gen(f)
            attrs['test_do_pay_%s' % f.lower()] = mcs.do_pay_gen(f)

        return super(HomeViewCaseMeta, mcs).__new__(mcs, name, bases, attrs)

    @classmethod
    def product_display_gen(mcs, formation):
        def fn(self):
            self.user.formation = formation
            self.user.save()
            r = self.client.get(reverse("tresorerie:home"),
                                HTTP_HOST="10.0.3.94", follow=True)
            self.assertEqual(200, r.status_code)

            for p in (
                    self.productFIG_1a,
                    self.productFIG_6m,
                    self.productFIP_1a,
                    self.productFIP_6m,
                    self.productAdhesion,
                    self.productFIG_1m):
                if p.autorisation[0] == 'ALL' or p.autorisation[0].lower() == formation.lower():
                    self.assertContains(r, "%i€" % (p.prix / 100))

        return fn

    @classmethod
    def do_pay_gen(mcs, formation):
        def fn(self):
            product = self.productFIG_1a
            transaction_uuid, price = self.prepare_payment(product, formation=formation, do_test=True)
            tok = self.create_token()

            r = self.client.post(
                reverse("tresorerie:pay", args=(product.id,)),
                data={
                    'uuid': transaction_uuid,
                    'price': price,
                    'stripeToken': tok.id,
                },
                HTTP_HOST="10.0.3.94",
                follow=True,
            )

            self.assertTemplateUsed(r, "tresorerie/history.html")
            self.assertContains(r, "%i€" % ((self.productAdhesion.prix + product.prix) / 100))

            # Check in database if everything is correct:
            user_s = LdapUser.get(pk=self.user.uid)
            self.assertIn(str(current_year()), user_s.cotiz)
            self.assertLessEqual(datetime.now() + timedelta(days=29), user_s.end_cotiz)

        return fn

class HomeViewCase(TestCase, metaclass=HomeViewCaseMeta):

    def setUp(self):
        self.user = create_full_user()
        self.user.cotiz = []
        try_delete_user(self.user.uid)
        self.user.save()
        self.client.login(username=self.user.uid, password=self.user.user_password)

        self.productFIG_1m = Product(
            nom="1 mois ResEl",
            prix=1000,
            type_produit="F",
            duree=1,
            autorisation="ALL",
        )
        self.productFIG_6m = Product(
            nom="6 mois ResEl",
            prix=5000,
            type_produit="F",
            duree=6,
            autorisation="FIG",
        )
        self.productFIG_1a = Product(
            nom="1 an ResEl",
            prix=8500,
            type_produit="F",
            duree=12,
            autorisation="FIG",
        )
        self.productFIP_6m = Product(
            nom="1 m6is ResEl FIP",
            prix=3100,
            type_produit="F",
            duree=6,
            autorisation="FIP",
        )
        self.productFIP_1a = Product(
            nom="1 an ResEl",
            prix=5100,
            type_produit="F",
            duree=12,
            autorisation="FIP",
        )
        self.productAdhesion = Product(
            nom="Adhesion au ResEl",
            prix=100,
            type_produit="A",
            duree=12,
            autorisation="ALL",
        )

        self.productFIG_1a.save()
        self.productFIG_6m.save()
        self.productFIG_1m.save()
        self.productFIP_1a.save()
        self.productFIP_6m.save()
        self.productAdhesion.save()

    def prepare_payment(self, product, formation="ANY", do_test=False):
        """
        Do all the first successful task to prepare a payment.

        :param product:
        :param do_test: should we test the code here ? Faster without
        :return:
        """
        # Ensure that this test is not run in release mode:
        self.assertIn("test", settings.STRIPE_API_KEY)

        stripe.api_key = settings.STRIPE_API_KEY
        self.user.formation = formation
        self.user.cotiz = []
        self.user.end_cotiz = datetime.today()
        self.user.save()

        # Choose product
        r = self.client.get(reverse("tresorerie:pay", args=(product.id,)),
                            HTTP_HOST="10.0.3.94", follow=True)

        if do_test:
            self.assertEqual(200, r.status_code)
            self.assertTemplateUsed(r, "gestion_personnes/personal_info.html")

        # Update user infos
        r = self.client.post(
            r.redirect_chain[0][0],
            data={
                'email': "email@email14.fr",
                'phone': "0123456789",
                'campus': "Brest",
                'building': "I10",
                'room': "14",
                'certify_truth': "certify_truth"
            },
            HTTP_HOST="10.0.3.94",
            follow=True,
        )
        if do_test:
            self.assertEqual(200, r.status_code)
            self.assertTemplateUsed(r, "tresorerie/recap.html")
            self.assertContains(r, "%i€" % (product.prix / 100))

            # Check if the user get a 2016 cotiz
            self.assertContains(r, "%i€" % (self.productAdhesion.prix / 100))

            # Check if the total is correct :
            self.assertContains(r, "%i€" % ((self.productAdhesion.prix + product.prix) / 100))

            # Check if the stripe public key is here
            self.assertContains(r, "%s" % settings.STRIPE_PUBLIC_KEY)

        return r.context["transaction"].uuid, r.context["transaction"].total_stripe

    @staticmethod
    def create_token(number='4242424242424242', exp_month=12, exp_year=2050, cvc='123'):
        """
        Create fastly a token from Stripe

        :param number:
        :param exp_month:
        :param exp_year:
        :param cvc:
        :return:
        """
        return stripe.Token.create(
            card={
                "number": number,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvc
            },
        )

    def test_no_need_to_pay(self):
        self.user.end_cotiz = datetime.now() + timedelta(days=50)
        self.user.save()

        r = self.client.get(reverse("tresorerie:home"),
                            HTTP_HOST="10.0.3.94", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'pages/home/home.html')

    def test_declined_card(self):
        product = self.productFIG_1a

        transaction_uuid, price = self.prepare_payment(product)

        # Create a token
        tok = self.create_token(number='4000000000000341')

        r = self.client.post(
            reverse("tresorerie:pay", args=(product.id,)),
            data={
                'uuid': transaction_uuid,
                'price': price,
                'stripeToken': tok.id,
            },
            HTTP_HOST="10.0.3.94",
            follow=True,
        )

        self.assertTemplateUsed(r, "tresorerie/recap.html")
        self.assertContains(r, "Votre carte a été refusée")

    def test_stripe_not_loaded(self):
        product = self.productFIG_1a

        transaction_uuid, price = self.prepare_payment(product)

        # Create a token create a request without a token
        r = self.client.post(
            reverse("tresorerie:pay", args=(product.id,)),
            data={
                'uuid': transaction_uuid,
                'price': price,
            },
            HTTP_HOST="10.0.3.94",
            follow=True,
        )

        self.assertTemplateUsed(r, "tresorerie/recap.html")
        self.assertContains(r, "Il semblerait que nous")

    def test_wrong_transaction_uuid(self):
        product = self.productFIG_1a
        transaction_uuid, price = self.prepare_payment(product)
        tok = self.create_token()

        r = self.client.post(
            reverse("tresorerie:pay", args=(product.id,)),
            data={
                'uuid': "e12a5a69-4ec4-4b44-83da-5c429fc6b0ad",
                'price': price,
                'stripeToken': tok.id,
            },
            HTTP_HOST="10.0.3.94",
            follow=True,
        )

        self.assertTemplateUsed(r, "tresorerie/recap.html")
        self.assertContains(r, "est produite lors de la commande.")

    def test_pay_twice_cotiz(self):

        product = self.productAdhesion
        transaction_uuid, price = self.prepare_payment(product)
        tok = self.create_token()

        user_s = LdapUser.get(pk=self.user.uid)
        user_s.cotiz = [current_year()]
        user_s.save()

        r = self.client.post(
            reverse("tresorerie:pay", args=(product.id,)),
            data={
                'uuid': transaction_uuid,
                'price': price,
                'stripeToken': tok.id,
            },
            HTTP_HOST="10.0.3.94",
            follow=True,
        )

        self.assertTemplateUsed(r, "tresorerie/recap.html")
        self.assertContains(r, "avez pas besoin de payer")

class ListProductCase(TestCase):
    # TODO : for the moment the test simply test that the page loads maybe do a bit more

    def setUp(self):
        self.user = create_full_user()
        self.user.cotiz = []
        try_delete_user(self.user.uid)
        self.user.save()
        # self.client.login(username=self.user.uid, password=self.user.user_password)

        self.productFIG_1m = Product(
            nom="1 mois ResEl",
            prix=1000,
            type_produit="F",
            duree=1,
            autorisation="ALL",
        )
        self.productFIG_6m = Product(
            nom="6 mois ResEl",
            prix=5000,
            type_produit="F",
            duree=6,
            autorisation="FIG",
        )
        self.productFIG_1a = Product(
            nom="1 an ResEl",
            prix=8500,
            type_produit="F",
            duree=12,
            autorisation="FIG",
        )
        self.productFIP_6m = Product(
            nom="6 mois ResEl FIP",
            prix=3100,
            type_produit="F",
            duree=6,
            autorisation="FIP",
        )
        self.productFIP_1a = Product(
            nom="1 an ResEl FIP",
            prix=5100,
            type_produit="F",
            duree=12,
            autorisation="FIP",
        )
        self.productAdhesion = Product(
            nom="Adhesion au ResEl",
            prix=100,
            type_produit="A",
            duree=12,
            autorisation="ALL",
        )

        self.productFIG_1a.save()
        self.productFIG_6m.save()
        self.productFIG_1m.save()
        self.productFIP_1a.save()
        self.productFIP_6m.save()
        self.productAdhesion.save()

    def test_simple_display(self):
        # Test if the user is not logged in
        r = self.client.get(reverse("tresorerie:prices"),
                            HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'tresorerie/list_product.html')


class TransactionDetailViewTest(TestCase):
    def setUp(self):
        self.user = create_full_user()
        self.user.cotiz = []
        try_delete_user(self.user.uid)
        self.user.save()
        self.client.login(username=self.user.uid, password=self.user.user_password)

        self.productFIG_1m = Product(
            nom="1 mois ResEl",
            prix=1000,
            type_produit="F",
            duree=1,
            autorisation="ALL",
        )
        self.productFIG_6m = Product(
            nom="6 mois ResEl",
            prix=5000,
            type_produit="F",
            duree=6,
            autorisation="FIG",
        )
        self.productFIG_1a = Product(
            nom="1 an ResEl",
            prix=8500,
            type_produit="F",
            duree=12,
            autorisation="FIG",
        )
        self.productFIP_6m = Product(
            nom="1 m6is ResEl FIP",
            prix=3100,
            type_produit="F",
            duree=6,
            autorisation="FIP",
        )
        self.productFIP_1a = Product(
            nom="1 an ResEl",
            prix=5100,
            type_produit="F",
            duree=12,
            autorisation="FIP",
        )
        self.productAdhesion = Product(
            nom="Adhesion au ResEl",
            prix=100,
            type_produit="A",
            duree=12,
            autorisation="ALL",
        )

        self.productFIG_1a.save()
        self.productFIG_6m.save()
        self.productFIG_1m.save()
        self.productFIP_1a.save()
        self.productFIP_6m.save()
        self.productAdhesion.save()

    def test_simple_display(self):
        # Create a fake transaction :
        t = Transaction()
        t.utilisateur = self.user.uid

        t.save()
        for p in [self.productFIG_1a, self.productAdhesion]:
            t.produit.add(p)
        t.save()

        r = self.client.get(reverse("tresorerie:transaction-detail",args=(t.uuid,)),
                            HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "tresorerie/transaction_detail.html")

