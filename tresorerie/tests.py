from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase

from gestion_personnes.tests import try_delete_user, create_full_user
from .models import Transaction


class HistoryViewCase(TestCase):
    def setUp(self):
        self.user =create_full_user()
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

    def test_no_need_to_pay(self):
        self.user.end_cotiz = datetime.now() + timedelta(days=50)
        self.user.save()

        r = self.client.get(reverse("tresorerie:home"),
                            HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, 'pages/home/home.html')
