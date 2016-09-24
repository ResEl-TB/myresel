import uuid
from datetime import datetime, timedelta

import django_rq
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _, get_language
from django.views.generic import View, ListView

import tresorerie.async_tasks as async_tasks
from fonctions import ldap, generic
from fonctions.decorators import resel_required, need_to_pay
from tresorerie.models import MonthlyPayment, Transaction, Product, StripeCustomer


class ChooseProduct(View):
    """
    Page to choose a product from
    """

    template_name = 'tresorerie/choose_product.html'

    @method_decorator(login_required)
    @method_decorator(need_to_pay)
    def dispatch(self, *args, **kwargs):
        return super(ChooseProduct, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):

        # All prices are in € cents
        user = request.ldap_user
        is_member = str(generic.current_year()) in user.cotiz
        formation = "FIG"

        if "fip" in user.formation.lower():
            formation = "FIP"

        adhesion = Product.objects.get(type_produit="A")
        products = list(Product.objects.filter(type_produit="F", autorisation=formation.upper()))
        products += list(Product.objects.filter(type_produit="F", autorisation="ALL"))
        products = sorted(products, key=lambda x: x.prix, reverse=True)  # So that the least expensive will have priority

        one_year = None
        six_month = None
        one_month = None
        # Small hack because I woudn't do that in the template
        for p in products:
            if p.duree == 12:
                one_year = p
            elif p.duree == 6:
                six_month = p
            elif p.duree == 1:
                one_month = p

        c = {
            'user': user,
            'is_member': is_member,
            'adhesion': adhesion,
            'one_year': one_year,
            'six_month': six_month,
            'one_month': one_month,
        }
        return render(request, self.template_name, context=c)


class Pay(View):
    """
        Page to make a payement
    """

    template_name = 'tresorerie/recap.html'

    @method_decorator(login_required)
    @method_decorator(need_to_pay)
    def dispatch(self, *args, **kwargs):
        return super(Pay, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Create a recap of the choosed product and make a payement
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        main_product = get_object_or_404(Product, pk=self.kwargs["product_id"])

        # Create a new transaction :
        transaction = Transaction()
        transaction.moyen = "CB"

        transaction.utilisateur = request.ldap_user.uid

        products = [main_product]

        # If the user is not member of the association :
        is_member = str(generic.current_year()) in request.ldap_user.cotiz

        if not is_member and main_product.type_produit != 'A':
            products.append(Product.objects.get(type_produit='A'))

        transaction.total = sum(product.prix for product in products) / 100
        transaction.total_stripe = sum(product.prix for product in products)
        transaction.full_name = ' + '.join(p.nom for p in products)
        c = {
            'main_product': main_product,
            'products': products,
            'transaction': transaction,
            'user': request.ldap_user,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        }

        request.session['transaction_uuid'] = str(transaction.uuid)
        request.session['transaction_total_stripe'] = transaction.total_stripe
        request.session['transaction_full_name'] = transaction.full_name

        request.session['products_id'] = [p.id for p in products]
        return render(request, self.template_name, c)

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_API_KEY
        user = request.ldap_user
        token = request.POST['stripeToken']
        given_uuid = uuid.UUID(request.POST['uuid'])

        transaction_uuid = uuid.UUID(request.session['transaction_uuid'])
        transaction_total = request.session['transaction_total_stripe']
        transaction_full_name = request.session['transaction_full_name']
        products_id = request.session['products_id']

        products = []
        for pk in products_id:
            products.append(Product.objects.get(pk=pk))

        is_member = str(generic.current_year()) in user.cotiz

        customer = StripeCustomer.retreive_or_create(user)
        customer.source = token
        customer.save()

        adhere = 'A' in (p.type_produit for p in products)

        if given_uuid != transaction_uuid:
            # TODO: show error message
            return HttpResponseRedirect(reverse('tresorerie:pay', self.kwargs["product_id"]))

        if adhere and is_member:
            # TODO: show error message
            return HttpResponseRedirect(reverse('tresorerie:pay', self.kwargs["product_id"]))

        try:
            charge = stripe.Charge.create(
                amount=transaction_total,
                currency="eur",
                description=transaction_full_name,
                customer=customer.id,
            )

            # Update the user internet access
            if adhere:
                user.cotiz += ' 2016'  # TODO: convert that to ldap list

            month_numbers = sum(p.duree for p in products if p.type_produit == 'F')

            date = datetime.now() + timedelta(days=month_numbers*30)
            user.end_cotiz = date
            user.save()

            # Insert the transaction in the database
            transaction = Transaction()
            transaction.uuid = transaction_uuid
            transaction.moyen = "CB"
            transaction.utilisateur = user.uid
            transaction.total = transaction_total / 100
            transaction.stripe_id = charge.id
            transaction.save()
            for p in products:
                transaction.produit.add(p)

            transaction.save()

            # TODO:
            # Generate notifications for the user
            # Asynchronously generate invoice and mail it to user & treasurer
            queue = django_rq.get_queue()
            queue.enqueue_call(
                async_tasks.generate_and_email_invoice,
                args=(request.user, transaction.total, transaction, get_language()),
            )

            messages.success(request, _("Votre accès a bien été réglé"))
            return HttpResponseRedirect(reverse('tresorerie:historique'))

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
            messages.error(request, _("Nous recevons actuellement trop de paiements simultanés, veuillez ré-essayer plus tard"))
            return HttpResponseRedirect(reverse('tresorerie:pay', self.kwargs["product_id"]))

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(request, _(
                "Impossible de contacter le serveur de paiement pour le moment, veuillez ré-essayer plus tard"))
            return HttpResponseRedirect(reverse('tresorerie:pay', self.kwargs["product_id"]))


class Home(View):
    """ Payment page """

    template_name = 'tresorerie/home.html'

    @method_decorator(resel_required)  # Maybe yes, maybe no ?
    @method_decorator(login_required)
    @method_decorator(need_to_pay)
    def dispatch(self, *args, **kwargs):
        return super(Home, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.ldap_user
        member = 'false'
        if str(generic.current_year()) in user.cotiz:
            member = 'true'
        request.session['mail'] = user.mail
        request.session['formation'] = user.formation
        request.session['member'] = member
        return render(request, self.template_name)

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
                transaction = Transaction.objects.create(
                    utilisateur=request.user,
                    total=1,
                    commentaire=_("Adhésion à l'Association")
                )

            days = 0

            if price == 1000 or price == 1100:
                # Single payment for 1 month
                days = 30

                transaction = Transaction.objects.create(
                    utilisateur=request.user,
                    total=10,
                    commentaire=_("Accès Internet pour 1 mois")
                )

            elif price == 1670 or price == 1770:
                # Monthly payment for 6 months access
                if request.session['formation'] == 'FIP':
                    comment = _("Accès Internet pour 1 an - 1ère mensualisation")
                    days = 12 * 30
                else:
                    comment = _("Accès Internet pour 6 mois - 1ère mensualisation")
                    days = 6 * 30

                MonthlyPayment.objects.create(
                    user=request.user,
                    months_to_pay=3,
                    months_paid=1,
                    customer=customer.id,
                    amount_to_pay=16.70
                )

                transaction = Transaction.objects.create(
                    utilisateur=request.user,
                    total=16.70,
                    commentaire=comment
                )

            elif price == 2840 or price == 2940:
                # Monthly payment for 1 year
                days = 12*30

                MonthlyPayment.objects.create(
                    user=request.user,
                    months_to_pay=3,
                    months_paid=1,
                    customer=customer.id,
                    amount_to_pay=28.40
                )

                transaction = Transaction.objects.create(
                    utilisateur=request.user,
                    total=28.40,
                    commentaire=_("Accès Internet pour 1 an - 1ère mensualisation")
                )

            elif price == 5000 or price == 5100:
                # Single payment for 6 months
                days = 6*30

                transaction = Transaction.objects.create(
                    utilisateur=request.user,
                    total=50,
                    commentaire=_("Accès Internet pour 6 mois")
                )

            elif price == 8500 or price == 8600:
                # Single payment for 1 year
                days = 12*30

                transaction = Transaction.objects.create(
                    utilisateur=request.user,
                    total=85,
                    commentaire=_("Accès Internet pour 1 an")
                )

            # Updating the LDAP to set the correct limit for the Internet Access
            ldap.cotisation(user=str(request.user), duree=days)

            # Asynchronously generate invoice and mail it to user & treasurer
            queue = django_rq.get_queue()
            queue.enqueue_call(
                async_tasks.generate_and_email_invoice,
                args=(request.user, price, transaction, get_language()),
            )

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


class History(ListView):
    """
    This view show to the user the history of his payements
    """

    template_name = 'tresorerie/history.html'
    context_object_name = 'transactions'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(History, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Transaction.objects.all().filter(utilisateur__exact=self.request.user).order_by('date')
