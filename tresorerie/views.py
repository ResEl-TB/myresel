from django.shortcuts import render
from django.views.generic import View, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

from .models import *
from fonctions import ldap, generic

# Create your views here.
class Home(View):
    """ Vue index de la section paiement. C'est cette page qui gère le paiement d'un user """

    template_name = 'paiement/home.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """ Vérification que la cotiz n'est pas déjà payée """

        user = ldap.search(DN_PEOPLE, '(&(uid=%s))' % request.user, ['cotiz', 'endcotiz'])[0]
        if 'cotiz' in user.entry_to_json().lower() and 'endcotiz' in user.entry_to_json().lower():
            # Les attributs 'cotiz' ET 'endcotiz' sont présents
            from datetime import datetime

            end_date = datetime.strptime(user.endcotiz[0], '%d/%m/%Y')
            if end_date > datetime.now():
                # Cotisation déjà payée
                messages.info(_("Vous avez déjà payé votre cotisation."))
                return HttpResponseRedirect(reverse('news'))

        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """ Plusieurs cas de figure
            1) L'utilisateur paye en intégralité sa cotisation :
                - 1 an - 86 €
                - 6 mois - 51 €
                - 1 mois - 11 €
            2) L'utilisateur paye en plusieurs fois la cotisation annuelle :
                - 3 fois - 29,40 € la première fois, 28,40 € les 2 autres fois
                - 5 fois - 18 € la première fois, 17 € les autres fois
                - 10 fois - 9,50 € la première fois, 8,50 € les autres
        """

        import stripe

        # Déf de la clé secrète pour Stripe
        stripe.api_key = 'sk_test_Uk3Qcg8o0OTj8VHAG6NovqR9'

        # Récupération du token Stripe
        token = request.POST['stripeToken']

        # Identification si l'user paye en une ou plusieurs fois
        type_paiement = request.POST['type_paiement']

        # Récupération du montant
        montant = request.POST['montant']

        if type_paiement == 'mensuel':
            """ Paiement mensuel """
            
            # Création du customer
            customer = stripe.Customer.create(source = token, description = "Cotisation ResEl")

            # Création de la mensualisation associée à l'user
            nb_m = request.POST['nb_mensualisations']
            user = Mensualisation.create(utilisateur = request.user, nb_m = nb_m, customer = customer.id)
            user.save(using = 'admin')

            try:
                # On facture l'user
                stripe.Charge.create(amount = montant, currency = "eur", customer = customer.id)

                # On met à jour le nombre de mensualités payées par l'user
                user.nb_p += 1
                user.save(using = 'admin')

                # On crée l'objet transaction dans l'interface de tréso admin
                t = Transaction.objects.create(
                    utilisateur = request.user, 
                    total = montant, 
                    commentaire = "Paiement mensuel en %d fois - Mensualité %d/%d" % (nb_m, user.nb_p, nb_m)
                )
                t.save(using = 'admin')

                # Récupération du type de produit et link du produit avec la transaction
                p = Produit.objects.using('admin').get(nom = 'cotisation')
                t.add(p)

                # Modif du LDAP
                ldap.cotisation(user = request.user, duree = 30)

            except stripe.error.CardError:
                # Carte refusée, on supprime la mensualisation si l'user veut recommencer
                user.delete()
                messages.error(_("Votre carte bancaire a été refusée, veuillez ré-essayer ou contacter un administrateur."))
                return render(request, self.template_name)

        else:
            """ Paiement unitaire """

            try:
                # On facture l'user
                stripe.Charge.create(amount = montant, currency = "eur", source = token, description = "Cotisation ResEl")

                # Types de cotisations
                COTISATIONS = {
                    11: ('Cotisation mensuelle', 30),
                    51: ('Cotisation 6 mois', 180),
                    86: ('Cotisation 1 an', 360)
                }

                # On crée l'objet transaction dans l'interface de tréso admin
                t = Transaction.objects.create(utilisateur = request.user, total = montant, commentaire = COTISATIONS[montant][0])
                t.save(using = 'admin')

                # Récupération du type de produit et link du produit avec la transaction
                p = Produit.objects.using('admin').get(nom = 'cotisation')
                t.add(p)

                # Modif du LDAP
                ldap.cotisation(user = request.user, duree = COTISATIONS[montant][1])

            except stripe.error.CardError:
                # Carte refusée
                messages.error(_("Votre carte bancaire a été refusée, veuillez ré-essayer ou contacter un administrateur."))
                return render(request, self.template_name)

class Historique(ListView):
    """ Vue qui affiche un historique des paiements de l'uitlisateur """

    template_name = 'paiement/historique.html'
    context_object_name = 'transactions'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Historique, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Transaction.objects.using('admin').all().filter(utilisateur__exact = self.request.user)