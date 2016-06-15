from django.views.generic import View, ListView, DetailView
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from fonctions import ldap, network
from .forms import *
from .models import *

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

# Create your views here.
class Home(View):
    """ Vue d'index, qui se charge de rediriger l'utilisateur sur la bonne page """

    template_name = 'myresel/home.html'

    def get(self, request, *args, **kwargs):
        # On regarde déjà si l'ip est une ip interne ou pas
        if not network.is_resel_ip(request.META['REMOTE_ADDR']):
            return HttpResponseRedirect(reverse('news'))

        # On vérifie que la machine n'est pas desactivée.
        # Si oui, on bascule vers la page de réactivation
        status = ldap.get_status(request.META['REMOTE_ADDR'])

        if status:
            # La machine existe dans le LDAP
            if status == 'inactive':
                # La machine est inactive
                return HttpResponseRedirect(reverse('gestion-machines:reactivation'))

            elif status == 'mauvais_campus':
                # La machine n'est pas dans le bon campus
                return HttpResponseRedirect(reverse('gestion-machines:changement-campus'))

            else:
                # La machine est active, on affiche la page de news
                return HttpResponseRedirect(reverse('news'))

        return HttpResponseRedirect(reverse('gestion-machines:ajout'))

class NewsListe(ListView):
    """ Vue appelée pour afficher les news au niveau du ResEl """

    template_name = 'myresel/news.html'
    context_object_name = 'derniers_billets'

    def get_queryset(self):
        return News.objects.all()

class Contact(View):
    """ Vue appelée pour contacter les admin en cas de soucis """

    template_name = 'myresel/contact.html'
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
            return HttpResponseRedirect(reverse('news'))
        return render(request, self.template_name, {'form': form})