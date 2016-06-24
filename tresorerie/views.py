from django.shortcuts import render
from django.views.generic import View, ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

from .models import MonthlyPayment, Transaction
from fonctions import ldap, generic
from fonctions.decorators import resel_required, unknown_machine, need_to_pay

class Home(View):
    """ Payment page """

    template_name = 'tresorerie/home.html'

    @method_decorator(resel_required)
    @method_decorator(login_required)
    @method_decorator(need_to_pay)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = ldap.search(settings.LDAP_DN_PEOPLE, '(&(uid=%s))' % str(request.user), ['formation', 'cotiz', 'mail'])
        if user:
            formation = 'unknown'
            if 'formation' in user[0].entry_to_json().lower():
                formation = user[0].formation[0]
            cotiz = user[0].cotiz[-1]
            member = 'false'
            if cotiz == str(generic.get_year()):
                member = 'true'
            request.session['mail'] = user[0].mail[0]
            request.session['formation'] = formation
            request.session['member'] = member
            return render(request, self.template_name)
        else:
            messages.error(request, _("Vous n'êtes pas inscrit dans notre base de données."))
            return HttpResponseRedirect(reverse('home'))

    def post(self, request, *args, **kwargs):
        import stripe

        # Stripe's secret key
        stripe.api_key = settings.STRIPE_API_KEY

        # Creating a Stripe customer
        token = request.POST['stripeToken']
        customer = stripe.Customer.create(source=token, description="Cotisation ResEl")

        # Getting the amount paid
        price = int(request.POST['price'])

        try:
            stripe.Charge.create(amount=price, currency="eur", customer=customer.id)            

            # Membership payment
            if request.session['member'] == 'false':
                Transaction.objects.using('admin').create(
                    utilisateur=request.user,
                    total=1,
                    commentaire=_("Adhésion à l'Association")
                )
            
            days = 0

            if price == 1000 or price == 1100:
                # Single payment for 1 month
                days = 30

                Transaction.objects.using('admin').create(
                    utilisateur=request.user,
                    total=10,
                    commentaire=_("Accès Internet pour 1 mois")
                )

            elif price == 1670 or price == 1770:
                # Monthly payment for 6 months access
                if request.session['formation'] == 'FIP':
                    comment = _("Accès Internet pour 1 an - 1ère mensualisation")
                    days = 12*30
                else:
                    comment = _("Accès Internet pour 6 mois - 1ère mensualisation")
                    days = 6*30

                MonthlyPayment.objects.using('admin').create(
                    user=request.user,
                    months_to_pay=3,
                    months_paid=1,
                    customer=customer.id,
                    amount_to_pay=16.70
                )

                Transaction.objects.using('admin').create(
                    utilisateur=request.user,
                    total=16.70,
                    commentaire=comment
                )

            elif price == 2840 or price == 2940:
                # Monthly payment for 1 year
                days = 12*30

                MonthlyPayment.objects.using('admin').create(
                    user=request.user,
                    months_to_pay=3,
                    months_paid=1,
                    customer=customer.id,
                    amount_to_pay=28.40
                )

                Transaction.objects.using('admin').create(
                    utilisateur=request.user,
                    total=28.40,
                    commentaire=_("Accès Internet pour 1 an - 1ère mensualisation")
                )

            elif price == 5000 or price == 5100:
                # Single payment for 6 months
                days = 6*30

                Transaction.objects.using('admin').create(
                    utilisateur=request.user,
                    total=50,
                    commentaire=_("Accès Internet pour 6 mois")
                )

            elif price == 8500 or price == 8600:
                # Single payment for 1 year
                days = 12*30

                Transaction.objects.using('admin').create(
                    utilisateur=request.user,
                    total=85,
                    commentaire=_("Accès Internet pour 1 an")
                )

            # Updating the LDAP to set the correct limit for the Internet Access
            #ldap.cotisation(utilisateur=str(request.user), duree=days)

            messages.success(request, _("Votre accès a bien été réglé"))
            return HttpResponseRedirect(reverse('home'))

        except stripe.error.CardError as e:
            code = e.json_body['error']['code']

            ERRORS = {
                'invalid_number': _("Votre numéro de carte n'est pas valide"),
                'invalid_expiry_month': _("Le mois d'expiration de votre carte n'est pas valide"),
                'invalid_expiry_year': _("L'année d'expiration de votre carte n'est pas valide"),
                'invalid_cvc': _("Le cryptogramme de votre carte n'est pas valide"),
                'incorrect_number': _("Votre numéro de carte est incorrect"),
                'expired_card': _("Votre carte a expiré"),
                'incorrect_cvc': _("Le cryptogramme de votre carte est incorrect"),
                'card_declined': _("Votre carte a été refusée"),
                'processing_error': _("Une erreur est survenue dans le traitement de votre demande")
            }

            messages.error(request, ERRORS[code])
            return render(request, self.template_name)
                
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(request, _("Trop d'essais pour le moment, veuillez ré-essayer plus tard"))
            return HttpResponseRedirect(reverse('home'))

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(request, _("Impossible de contacter le serveur de paiement pour le moment, veuillez ré-essayer plus tard"))
            return HttpResponseRedirect(reverse('home'))

class Historique(ListView):
    """ Vue qui affiche un historique des paiements de l'uitlisateur """

    template_name = 'tresorerie/historique.html'
    context_object_name = 'transactions'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Historique, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Transaction.objects.using('admin').all().filter(utilisateur__exact = self.request.user).order_by('date')