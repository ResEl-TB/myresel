from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator

from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView

from pages.forms import ContactForm
from fonctions import network, ldap, decorators
from pages.models import News


class Home(View):
    """
    La première vue que l'utilisateur va ouvrir lorsqu'il arrive sur le site. L'objectif de cette page est d'être d'être
    la plus simple pour tous les types d'utilisations.

    Du fait des différentes origines et objectifs des utilisateurs il y a plusieurs vues possible :
        - Nouvel utilisateur sur le campus, on lui propose de s'inscrire
        - Utilisateur connecté sur le campus, on lui propose des options pour son compte
        - la personne exterieure qui veut en savoir plus sur le ResEl
        - L'utilisateur à l'exterieur qui veut avoir des infos sur son compte
    """

    template_name = 'pages/home.html'

    @method_decorator(decorators.correct_vlan)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Check if the ip is inside the network :
        if not network.is_resel_ip(request.META['REMOTE_ADDR']):
            return render(request, self.template_name)

        # On vérifie que la machine n'est pas desactivée.
        # Si oui, on bascule vers la page de réactivation
        computer_status = ldap.get_status(request.META['REMOTE_ADDR'])

        if computer_status:
            # La machine existe dans le LDAP
            if computer_status == 'inactive':
                # La machine est inactive
                return HttpResponseRedirect(reverse('gestion-machines:reactivation'))

            elif computer_status == 'wrong_campus':
                # La machine n'est pas dans le bon campus
                return HttpResponseRedirect(reverse('gestion-machines:changement-campus'))

        return render(request, self.template_name)


class NewsListe(ListView):
    """ Vue appelée pour afficher les news au niveau du ResEl """

    template_name = 'pages/news.html'
    context_object_name = 'derniers_billets'

    def get_queryset(self):
        return News.objects.all()


class Contact(View):
    """ Vue appelée pour contacter les admin en cas de soucis """

    template_name = 'pages/contact.html'
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Envoi d'un mail à support
            mail = EmailMessage(
                subject = "Message de la part d'un utilisateur",
                body = "%(nom)s souhaite vous contacter\n\nChambre : %(chambre)s\nDemande :\n%(demande)s" % {'nom': form.cleaned_data['nom'], 'chambre': form.cleaned_data['chambre'], 'demande': form.cleaned_data['demande']},
                from_email = "myresel@resel.fr",
                reply_to = [form.cleaned_data['mail']],
                to = ["support@resel.fr"],
            )
            mail.send()

            messages.success(_("Votre demande a bien été envoyée aux administrateurs. L'un d'eux vous répondra d'ici peu."))
            return HttpResponseRedirect(reverse('pages:news'))
        return render(request, self.template_name, {'form': form})
