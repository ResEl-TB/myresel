from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from gestion_personnes.tests import try_delete_user, try_delete_old_user, create_full_user


class ContactCase(TestCase):
    def test_loggedout_contact(self):
        get_page = self.client.get(reverse("contact"),
                                   HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, get_page.status_code)

        post_message = self.client.post(
            reverse("contact"), data={
                'nom': 'Lolo',
                'chambre': "I10 14",
                'mail': "123soleil@fds.sd",
                'demande': "Test post, please ignore",
            },
            HTTP_HOST="10.0.3.99", follow=True
        )
        self.assertEqual(200, get_page.status_code)
        self.assertEqual(1, len(mail.outbox))


    def test_loggedin_contact(self):
        try_delete_user("amanoury")
        try_delete_old_user("amanoury")
        self.user = create_full_user()
        self.user.save()
        self.client.login(username="amanoury", password="blah")
        get_page = self.client.get(reverse("contact"),
                                   HTTP_HOST="10.0.3.99", follow=True)
        self.assertEqual(200, get_page.status_code)

        form = get_page.context['form']
        data = form.initial
        data['demande'] = "Test post, please ignore"
        post_message = self.client.post(
            reverse("contact"), data=data,
            HTTP_HOST="10.0.3.99", follow=True
        )
        self.assertEqual(200, get_page.status_code)
