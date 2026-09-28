import yaml

from django.core import mail
from django.urls import reverse
from django.test import SimpleTestCase, TestCase

from gestion_personnes.tests import try_delete_user, try_delete_old_user, create_full_user
from pages.models import News
from pages.views import StatusPageXhr
from wiki.models import Category, Link


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
                'captcha': 'Paul Fridel',
            },
            HTTP_HOST="10.0.3.99", follow=True
        )
        self.assertEqual(200, get_page.status_code)
        self.assertEqual(1, len(mail.outbox))

    def test_bad_captcha(self):
        get_page = self.client.get(reverse("contact"),
                                   HTTP_HOST="10.0.3.99", follow=True)
        post_message = self.client.post(
            reverse("contact"), data={
                'nom': 'Lolo',
                'chambre': "I10 14",
                'mail': "123soleil@fds.sd",
                'demande': "Test post, please ignore",
                'captcha': 'Blah blah',
            },
            HTTP_HOST="10.0.3.99", follow=True
        )
        self.assertEqual(200, get_page.status_code)
        self.assertEqual(0, len(mail.outbox))


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
        data['captcha'] = "Fridel Paul"
        post_message = self.client.post(
            reverse("contact"), data=data,
            HTTP_HOST="10.0.3.99", follow=True
        )
        self.assertEqual(200, get_page.status_code)

class NewsCase(TestCase):
    def setUp(self):
        self.news = []
        for i in range(5):
            n = News(
                title="Random title %i" % i,
                content="Random content %i" % i,
            )

            n.save()
            self.news.append(n)

    def test_simple_load(self):
        r = self.client.get(reverse("news"),
                                   HTTP_HOST="10.0.3.94", follow=True)

        # news list page
        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/news.html")
        for n in self.news:
            self.assertContains(r, n.title)

        # News detail page
        r = self.client.get(reverse("piece-of-news", args=[self.news[0].pk]),
                            HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/piece_of_news.html")
        self.assertContains(r, self.news[0].title)


class HomeViewCase(TestCase):
    def setUp(self):
        cat = Category()
        cat.name = "Services"
        cat.save()

        ln = Link()
        ln.name = "Dumb link to a site"
        ln.url = "https://wiki.resel.fr/"
        ln.description = "This is simple link to a wonderful website"
        ln.category = cat
        ln.save()

        self.ln = ln

    def test_simple_load(self):
        r = self.client.get(reverse("home"),
                                   HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/home/home.html")
        self.assertContains(r, self.ln.name)
        self.assertContains(r, self.ln.description)
        self.assertContains(r, self.ln.url)

class ServiceViewCase(TestCase):
    def setUp(self):
        cat = Category()
        cat.name = "Services"
        cat.save()

        ln = Link()
        ln.name = "Another dumb link to a site"
        ln.url = "https://wiki.resel.fr/"
        ln.description = "This is simple link to a questionable website"
        ln.category = cat
        ln.save()

        self.ln = ln

    def test_simple_load(self):
        r = self.client.get(reverse("services"),
                                   HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/service.html")
        self.assertContains(r, self.ln.name)
        self.assertContains(r, self.ln.description)
        self.assertContains(r, self.ln.url)

class StatusInternetFailoverCase(SimpleTestCase):
    def calculate_status(self, down_hosts=(), service_incidents=()):
        with open('myresel/icinga_status.yml', 'rb') as config:
            services = yaml.safe_load(config)
        configured_hosts = {
            host for campus in services['campuses']
            for section in campus['services'].values()
            for service in section for host in service.get('_hosts', [])
        }
        hosts = {
            'results': [
                {'attrs': {'name': host, 'state': int(host in down_hosts)}}
                for host in configured_hosts
            ],
        }
        incidents = {
            'results': [
                {'attrs': {'name': name, 'state': state}, 'joins': {'host': {'name': host}}}
                for host, name, state in service_incidents
            ],
        }
        StatusPageXhr.calc_scores(services, incidents, hosts)
        return services

    def test_isp_failover_per_campus(self):
        for campus_name, suffix in [('brest', 'br'), ('rennes', 're')]:
            ielo, moji = 'gw-ielo-' + suffix, 'gw-moji-' + suffix
            cases = [
                ([], 0, 'success', ['success', 'success']),
                ([ielo], 2, 'warning', ['danger', 'success']),
                ([moji], 2, 'warning', ['success', 'danger']),
                ([ielo, moji], 4, 'danger', ['danger', 'danger']),
            ]
            for down_hosts, score, status, provider_statuses in cases:
                with self.subTest(campus=campus_name, down=down_hosts):
                    services = self.calculate_status(down_hosts)
                    self.assertEqual(score, services['global_status_score'])
                    self.assertEqual(status, services['global_status'])
                    campus = next(c for c in services['campuses'] if c['name'] == campus_name)
                    self.assertEqual(provider_statuses, [
                        provider['status'] for provider in campus['services']['internet-access']
                    ])

    def test_provider_failures_on_different_campuses_do_not_mean_total_outage(self):
        services = self.calculate_status(['gw-ielo-br', 'gw-moji-re'])
        self.assertEqual(2, services['global_status_score'])
        self.assertEqual('warning', services['global_status'])

    def test_nantes_single_provider_failure_means_total_outage(self):
        services = self.calculate_status(['internet-nantes'])
        campus = next(c for c in services['campuses'] if c['name'] == 'nantes')
        providers = campus['services']['internet-access']
        self.assertEqual(1, len(providers))
        self.assertEqual('danger', providers[0]['status'])
        self.assertEqual(4, services['global_status_score'])
        self.assertEqual('danger', services['global_status'])

    def test_service_incidents_are_included_in_isp_failover(self):
        cases = [
            ([], [('gw-ielo-br', 'ping', 2)], 2),
            (['gw-ielo-br'], [('gw-moji-br', 'ping', 1)], 2),
            (['gw-ielo-br'], [('gw-moji-br', 'ping', 2)], 4),
            ([], [('gw-ielo-br', 'apt', 2)], 0),
        ]
        for down_hosts, incidents, score in cases:
            with self.subTest(down=down_hosts, incidents=incidents):
                services = self.calculate_status(down_hosts, incidents)
                self.assertEqual(score, services['global_status_score'])

    def test_other_services_keep_their_existing_severity(self):
        cases = [
            (['kuma'], 4, 'danger'),
            (['kim'], 2, 'warning'),
            (['lena'], 1, 'success'),
            (['kuma', 'gw-ielo-br'], 4, 'danger'),
        ]
        for down_hosts, score, status in cases:
            with self.subTest(down=down_hosts):
                services = self.calculate_status(down_hosts)
                self.assertEqual(score, services['global_status_score'])
                self.assertEqual(status, services['global_status'])

    def test_empty_or_unmonitored_isp_group_is_not_a_total_outage(self):
        for providers in ([], [{'name': 'isp-without-metrics'}]):
            with self.subTest(providers=providers):
                services = {'exclusions': [], 'campuses': [{
                    'services': {'internet-access': providers},
                }]}
                StatusPageXhr.calc_scores(services, {'results': []})
                self.assertEqual(0, services['global_status_score'])


class StatusMissingMetricsCase(SimpleTestCase):
    def test_missing_hosts_are_unknown(self):
        for configured_hosts in (None, [], ['missing'], ['healthy', 'missing']):
            with self.subTest(hosts=configured_hosts):
                service = {'_hosts': configured_hosts}
                score = StatusPageXhr.set_service_status(
                    {'results': []}, service, [],
                    {'results': [{'attrs': {'name': 'healthy', 'state': 0}}]},
                )
                self.assertEqual(-1, score)
                self.assertEqual('default', service['status'])
                self.assertEqual('Pas de métriques', service['status_text'])
                self.assertNotIn('_hosts', service)

    def test_unknown_host_does_not_provide_failover(self):
        for state, expected_status in [(0, 'success'), (1, 'default')]:
            with self.subTest(state=state):
                service = {'_hosts': ['known', 'missing'], '_hosts_failover': True}
                StatusPageXhr.set_service_status(
                    {'results': []}, service, [],
                    {'results': [{'attrs': {'name': 'known', 'state': state}}]},
                )
                self.assertEqual(expected_status, service['status'])

    def test_unavailable_supervision_is_unknown_globally(self):
        services = {'exclusions': [], 'campuses': [{
            'services': {'internet-access': [{'_hosts': ['isp']}]}},
        ]}
        StatusPageXhr.calc_scores(services, {'results': []}, {})
        self.assertEqual('default', services['global_status'])
        self.assertEqual('Pas de métriques', services['global_status_text'])


class StatusViewCase(TestCase):

    def test_host_status_is_included_in_service_status(self):
        service = {
            'name': 'moji-brest',
            'level': 1,
            '_hosts': ['gw-moji-br'],
        }
        hosts = {
            'results': [{
                'attrs': {'name': 'gw-moji-br', 'state': 1},
            }],
        }

        score = StatusPageXhr.set_service_status(
            {'results': []},
            service,
            [],
            hosts,
        )

        self.assertEqual(2, score)
        self.assertEqual('danger', service['status'])

    def test_isp_host_failover(self):
        cases = [
            (True, ['isp-a', 'isp-b'], [], 0, 'success'),
            (True, ['isp-a', 'isp-b'], ['isp-a'], 0, 'success'),
            (True, ['isp-a', 'isp-b'], ['isp-b'], 0, 'success'),
            (True, ['isp-a', 'isp-b'], ['isp-a', 'isp-b'], 2, 'danger'),
            (True, ['isp-a'], ['isp-a'], 2, 'danger'),
            (False, ['isp-a', 'isp-b'], ['isp-a'], 2, 'danger'),
            (True, [], [], -1, 'default'),
        ]
        for failover, configured_hosts, down_hosts, expected_score, expected_status in cases:
            with self.subTest(failover=failover, hosts=configured_hosts, down=down_hosts):
                service = {
                    'name': 'isp',
                    'level': 1,
                    '_hosts': configured_hosts,
                    '_hosts_failover': failover,
                }
                hosts = {
                    'results': [
                        {'attrs': {'name': host, 'state': int(host in down_hosts)}}
                        for host in configured_hosts
                    ],
                }

                score = StatusPageXhr.set_service_status(
                    {'results': []}, service, [], hosts,
                )

                self.assertEqual(expected_score, score)
                self.assertEqual(expected_status, service['status'])

    def test_isp_failover_includes_service_incidents(self):
        for state, expected_status in [(0, 'success'), (1, 'warning'), (2, 'danger')]:
            with self.subTest(state=state):
                service = {
                    'name': 'isp',
                    'level': 2,
                    '_hosts': ['isp-a', 'isp-b'],
                    '_hosts_failover': True,
                }
                incidents = {'results': []}
                if state:
                    incidents['results'].append({
                        'attrs': {'name': 'ping', 'state': state},
                        'joins': {'host': {'name': 'isp-b'}},
                    })
                hosts = {
                    'results': [
                        {'attrs': {'name': 'isp-a', 'state': 1}},
                        {'attrs': {'name': 'isp-b', 'state': 0}},
                    ],
                }

                score = StatusPageXhr.set_service_status(
                    incidents, service, [], hosts,
                )

                self.assertEqual(2 * state, score)
                self.assertEqual(expected_status, service['status'])

    def test_simple_load(self):
        r = self.client.get(reverse("network-status"),
                            HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
        self.assertTemplateUsed(r, "pages/network_status.html")

    def test_simple_load_api(self):
        r = self.client.get(reverse("network-status-xhr"),
                            HTTP_HOST="10.0.3.94", follow=True)

        self.assertEqual(200, r.status_code)
