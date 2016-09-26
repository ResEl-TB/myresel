# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase

from gestion_personnes.tests import create_full_user, try_delete_user
from tresorerie.models import Transaction, Product


class HistoryViewCase(TestCase):
    def setUp(self):
        self.user = create_full_user()
        try_delete_user(self.user.uid)
        self.user.save()
        self.client.login(username=self.user.uid, password=self.user.user_password)

    def test_no_transactions(self):
        r = self.client.get(reverse("tresorerie:historique"),
                                   HTTP_HOST="10.0.3.199", follow=True)
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
                            HTTP_HOST="10.0.3.199", follow=True)
        self.assertNotContains(r, "Pas de paiements trouvés dans la base de données.")
        self.assertTemplateUsed(r, "tresorerie/history.html")
        for p in transactions_values:
            self.assertContains(r, str(p))


class HomeViewCase(TestCase):
    def setUp(self):
        self.user = create_full_user()
        self.user.cotiz = ""
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

    def test_no_need_to_pay(self):
        self.user.end_cotiz = datetime.now() + timedelta(days=50)
        self.user.save()

        r = self.client.get(reverse("tresorerie:home"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'pages/home/home.html')

    def test_fip(self):
        self.user.formation = "FIP"
        self.user.save()
        r = self.client.get(reverse("tresorerie:home"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)

        for p in (
                self.productFIP_1a,
                self.productFIP_6m,
                self.productAdhesion,
                self.productFIG_1m):
            self.assertContains(r, "%i€" % (p.prix/100))

    def test_fig(self):
        self.user.formation = "FIG"
        self.user.save()
        r = self.client.get(reverse("tresorerie:home"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)

        for p in (
                self.productFIG_1a,
                self.productFIG_6m,
                self.productAdhesion,
                self.productFIG_1m):
            self.assertContains(r, "%i€" % (p.prix/100))

    def test_any(self):
        self.user.formation = "ANY"
        self.user.save()
        r = self.client.get(reverse("tresorerie:home"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)

        for p in (
                self.productFIG_1a,
                self.productFIG_6m,
                self.productAdhesion,
                self.productFIG_1m):
            self.assertContains(r, "%i€" % (p.prix/100))

    def test_recap_get(self):
        self.user.formation = "ANY"
        self.user.cotiz = ""
        self.user.save()

        product = self.productFIG_1a

        r = self.client.get(reverse("tresorerie:pay", args=(product.id,)),
                            HTTP_HOST="10.0.3.99", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "tresorerie/recap.html")
        self.assertContains(r, "%i€" % (product.prix/100))

        # Check if the user get a 2016 cotiz
        self.assertContains(r, "%i€" % (self.productAdhesion.prix / 100))

        # Check if the total is correct :
        self.assertContains(r, "%i€" % ((self.productAdhesion.prix+product.prix) / 100))