import uuid
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import django_rq
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _, get_language
from django.views.generic import DetailView, View, ListView

import tresorerie.async_tasks as async_tasks
from fonctions import generic
from fonctions.decorators import need_to_pay
from tresorerie.models import Transaction, Product, StripeCustomer


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
        is_member = user.is_member()
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
            'formation': formation
        }
        request.session['update'] = False
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
        # Check if info where updated
        product_id = self.kwargs["product_id"]
        updated = request.session.get('update', False)
        if not updated:
            messages.warning(request,
                          _("Veuillez vérifier que vos informations personnelles soient correctes."))
            return HttpResponseRedirect(
                reverse("gestion-personnes:personal-infos")
                + "?next="
                + quote_plus(reverse('tresorerie:pay', kwargs={'product_id': product_id}))
            )

        main_product = get_object_or_404(Product, pk=product_id)

        # Create a new transaction :
        transaction = Transaction()
        transaction.moyen = "CB"

        transaction.utilisateur = request.ldap_user.uid

        products = [main_product]

        # If the user is not member of the association :
        is_member = request.ldap_user.is_member()

        if not is_member and main_product.type_produit != 'A':
            products.append(Product.objects.get(type_produit='A'))

        formation = "FIG"

        if "fip" in request.ldap_user.formation.lower():
            formation = "FIP"

        if formation == "FIG" and main_product.autorisation == "FIP":
            raise PermissionDenied

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

        transaction_uuid = uuid.UUID(request.session['transaction_uuid'])
        transaction_total = request.session['transaction_total_stripe']
        transaction_full_name = request.session['transaction_full_name']
        products_id = request.session['products_id']
        main_product_id = self.kwargs["product_id"]
        products = []
        for pk in products_id:
            products.append(Product.objects.get(pk=pk))

        try:
            token = request.POST['stripeToken']
            given_uuid = uuid.UUID(request.POST['uuid'])
        except MultiValueDictKeyError:
            messages.error(request, _("Veuillez activer le javascript pour effectuer le paiement. En cas de problème n'hésitez pas à nous contacter."))
            return HttpResponseRedirect(reverse('tresorerie:pay', kwargs={'product_id': main_product_id}))

        customer = StripeCustomer.retrieve_or_create(user)
        customer.source = token
        customer.save()

        adhere = 'A' in (p.type_produit for p in products)

        if given_uuid != transaction_uuid:
            # TODO: show error message
            return HttpResponseRedirect(reverse('tresorerie:pay', kwargs={'product_id': main_product_id}))

        if adhere and user.is_member():
            messages.error(request, _("Vous êtes déjà membre de l'association, vous n'avez pas besoin de payer à nouveau la cotisation."))
            return HttpResponseRedirect(reverse('tresorerie:pay', kwargs={'product_id': main_product_id}))

        try:
            charge = stripe.Charge.create(
                amount=transaction_total,
                currency="eur",
                description=transaction_full_name,
                customer=customer.id,
            )

            # TODO: move everything here somewhere more appropriate
            # Update the user internet access
            if adhere:
                year = generic.current_year()
                # Delete blacklist and add this year:
                user.cotiz = [c for c in user.cotiz if c.lower() != "none" + str(year)] + [str(year)]

            month_numbers = sum(p.duree for p in products if p.type_produit == 'F')

            # For users who don't have an end_cotiz field
            if user.end_cotiz is None:
                user.end_cotiz = datetime.now()

            offset = max(user.end_cotiz, datetime.now())
            user.end_cotiz = offset + timedelta(days=month_numbers*30)
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

            queue = django_rq.get_queue()
            queue.enqueue_call(
                async_tasks.generate_and_email_invoice,
                args=(request.ldap_user, transaction, get_language()),
            )

            messages.success(request, _("Vous venez de payer votre accès au ResEl, vous devriez recevoir sous peu un email avec votre facture."))
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
        return Transaction.objects.all().filter(utilisateur__exact=self.request.user).order_by('date_creation')


class TransactionDetailView(DetailView):

    model = Transaction
    template_name = "tresorerie/transaction_detail.html"
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context = super(TransactionDetailView, self).get_context_data(**kwargs)
        context['user'] = self.request.ldap_user
        context['main_product'] = context['transaction'].produit.all()[0]
        context['products'] = context['transaction'].produit.all()

        return context


class ListProducts(View):
    """
    View to list the different product available
    """

    template_name = 'tresorerie/list_product.html'

    def get(self, request, *args, **kwargs):

        adhesion = Product.objects.get(type_produit="A")
        products_FIP = list(Product.objects.filter(type_produit="F", autorisation="FIP"))
        products_FIP += list(Product.objects.filter(type_produit="F", autorisation="ALL"))
        products_FIP = sorted(products_FIP, key=lambda x: x.prix, reverse=True)  # So that the least expensive will have priority

        products_FIG = list(Product.objects.filter(type_produit="F", autorisation="ALL"))
        products_FIG = sorted(products_FIG, key=lambda x: x.prix, reverse=True)

        one_year_FIP = None
        six_month_FIP = None
        one_month_FIP = None
        one_year_FIG = None
        six_month_FIG = None
        one_month_FIG = None

        # Small hack because I woudn't do that in the template
        for p in products_FIP:
            if p.duree == 12:
                one_year_FIP = p
            elif p.duree == 6:
                six_month_FIP = p
            elif p.duree == 1:
                one_month_FIP = p

        for p in products_FIG:
            if p.duree == 12:
                one_year_FIG = p
            elif p.duree == 6:
                six_month_FIG = p
            elif p.duree == 1:
                one_month_FIG = p

        c = {
            'adhesion': adhesion,
            'one_year_FIP': one_year_FIP,
            'six_month_FIP': six_month_FIP,
            'one_month_FIP': one_month_FIP,
            'one_year_FIG': one_year_FIG,
            'six_month_FIG': six_month_FIG,
            'one_month_FIG': one_month_FIG,
        }
        return render(request, self.template_name, context=c)
