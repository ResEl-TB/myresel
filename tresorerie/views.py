# -*- coding: utf-8 -*-
import uuid
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import quote_plus

import django_rq
import logging
import stripe
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _, get_language
from django.views.generic import DetailView, View, ListView

import tresorerie.async_tasks as async_tasks
from fonctions import generic
from fonctions.decorators import need_to_pay, able_to_pay
from tresorerie.models import Transaction, Product, StripeCustomer

logger = logging.getLogger("default")


class ChooseProduct(View):
    """
    Page to choose a product from
    """

    template_name = 'tresorerie/choose_product.html'

    @method_decorator(login_required)
    @method_decorator(able_to_pay)
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
    Page which make the actual payment
    There is not coming back from that page. An error here is critical.
    So be very careful!
    """

    template_name = 'tresorerie/recap.html'

    @method_decorator(login_required)
    @method_decorator(able_to_pay)
    @method_decorator(need_to_pay)
    def dispatch(self, *args, **kwargs):
        return super(Pay, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Create a recap of the chosen product and make a payment
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
        customer = StripeCustomer.retrieve_or_create(request.ldap_user)

        payment_intent = stripe.PaymentIntent.create(
            amount=transaction.total_stripe,
            currency="eur",
            description=transaction.full_name,
            customer=customer.id,
        )

        c = {
            'main_product': main_product,
            'products': products,
            'transaction': transaction,
            'user': request.ldap_user,
            'public_key': settings.STRIPE_PUBLIC_KEY,
            'payment_intent': json.dumps(payment_intent)
        }

        request.session['transaction_uuid'] = str(transaction.uuid)
        request.session['transaction_total_stripe'] = transaction.total_stripe
        request.session['transaction_full_name'] = transaction.full_name
        request.session['payment_intent'] = payment_intent.id

        request.session['products_id'] = [p.id for p in products]
        return render(request, self.template_name, c)

    def post(self, request, *args, **kwargs):
        user = request.ldap_user

        transaction_uuid = uuid.UUID(request.session['transaction_uuid'])
        transaction_total = request.session['transaction_total_stripe']
        transaction_full_name = request.session['transaction_full_name']
        payment_intent = stripe.PaymentIntent.retrieve(request.session['payment_intent'])
        products_id = request.session['products_id']
        main_product_id = self.kwargs["product_id"]
        products = []

        try:
            Transaction.objects.get(uuid=transaction_uuid)
            return HttpResponseRedirect(reverse('tresorerie:historique'))
        except ObjectDoesNotExist as e:
            pass

        for pk in products_id:
            products.append(Product.objects.get(pk=pk))

        try:
            given_uuid = uuid.UUID(request.POST['uuid'])
        except MultiValueDictKeyError as e:
            logger.error("%s a tenté de contourner le paiement. Erreur: %s" % (user.uid, e),
                    extra={
                        "transaction_uuid": transaction_uuid,
                        "transaction_name": transaction_full_name,
                        "uid": user.uid,
                        "ip": request.network_data['ip'],
                        "end_internet": user.end_cotiz,
                        'message_code': 'STRIPE_FIREWALL_ERROR',
                    })
            messages.error(request, _("Il semblerait que vous ayez tenté de contourner le "
                                      "paiement. Cette action a été signalée."))
            return HttpResponseRedirect(reverse('tresorerie:pay', kwargs={'product_id': main_product_id}))

        adhere = 'A' in (p.type_produit for p in products)

        if given_uuid != transaction_uuid:
            # TODO: show error message
            logger.warning(
                "L'uuid d'une transaction n'est pas correct. donné : %s attendu : %s" % (given_uuid, transaction_uuid),
                extra={
                    "given_uuid": given_uuid,
                    "transaction_uuid": transaction_uuid,
                    'message_code': 'INVALID_TRANSACTION_UUID',
                }
            )
            messages.error(request, _("Une erreur s'est produite lors de la commande. Veuillez contacter un administrateur."))
            return HttpResponseRedirect(reverse('tresorerie:pay', kwargs={'product_id': main_product_id}))

        payment_status = payment_intent.status

        if payment_status == 'succeeded':

            # TODO: move everything here somewhere more appropriate
            # Update the user internet access
            if adhere:
                year = generic.current_year()
                # Delete blacklist and add this year:
                user.cotiz = [c for c in user.cotiz if c.lower() != "none" + str(year)] + [str(year)]

            month_numbers = sum(p.duree for p in products if p.type_produit == 'F')

            # For users who don't have an end_cotiz field
            if user.end_cotiz is None:
                user.end_cotiz = datetime.now().astimezone()

            start = max(user.end_cotiz, datetime.now().astimezone())
            user.end_cotiz = start + relativedelta(months=month_numbers)
            user.save()

            # Insert the transaction in the database
            transaction = Transaction()
            transaction.uuid = transaction_uuid
            transaction.moyen = "CB"
            transaction.utilisateur = user.uid
            transaction.total = transaction_total / 100
            transaction.stripe_id = payment_intent.id
            transaction.save()  # Because a UUID is needed before adding products
            for p in products:
                # pylint: disable=no-member
                transaction.produit.add(p)

            transaction.save()


            # Gather information and launch tasks for sending invoice
            user_datas = {
                'first_name': request.ldap_user.first_name,
                'last_name' : request.ldap_user.last_name,
                'uid': request.ldap_user.uid,
                'email' : request.ldap_user.mail,
                'address' : request.ldap_user.postal_address,
            }
            transaction_datas = {
                'uuid': transaction.uuid,
                'date_creation': transaction.date_creation,
                'date_paiement': transaction.date_creation,
                'statut': transaction.statut,
                'moyen': transaction.get_moyen_display(),
                'total': transaction.total,
                'admin': transaction.admin,
                'categories': [
                    {'name': cat, 'products': prods} for cat, prods in transaction.get_products_by_cat()
                ],
            }
            user_lang = get_language().split('-')[0]

            logger.info(
                "Paiement validé par le système, uid: %s, uuid: %s, stripe id : %s" %(request.ldap_user.uid, transaction.uuid, transaction.stripe_id),
                extra={
                    "uid": request.ldap_user.uid,
                    "transaction_uuid": transaction.uuid,
                    "transaction_stripe_id": transaction.stripe_id,
                    'message_code': 'SUCCESSFUL_PAYMENT',
                }
            )
            messages.success(request, _("Vous venez de payer votre accès au ResEl, vous devriez recevoir sous peu un email avec votre facture."))

            # Send a french version for treasurer and one in the user's language
            try:
                queue = django_rq.get_queue()
                if user_lang == 'fr':
                    queue.enqueue_call(
                        async_tasks.generate_and_email_invoice,
                        args=(user_datas, transaction_datas,
                            'fr', 'user-treasurer'),
                    )
                else:
                    queue.enqueue_call(
                        async_tasks.generate_and_email_invoice,
                        args=(user_datas, transaction_datas,
                            'fr', 'treasurer'),
                    )
                    queue.enqueue_call(
                        async_tasks.generate_and_email_invoice,
                        args=(user_datas, transaction_datas,
                            user_lang, 'user'),
                    )
            except Exception as e:
                logger.error(
                    "ERROR_ENQUEING_INVOICE: "
                    "Une erreur s'est produite lors de l'ajout de la facture "
                    "à la queue de facturation. L'utilisateur sera bien "
                    "débité, mais il ne recevra pas de facture par mail. "
                    "uid: %s "
                    "uuid: %s "
                    "stripe_id: %s "
                    "error: %s " % (
                        request.ldap_user.uid,
                        transaction.uuid,
                        transaction.stripe_id,
                        e,
                    ),
                    extra={
                        'uid': request.ldap_user.uid,
                        'transaction_uuid': transaction.uuid,
                        'transaction_stripe_id': transaction.stripe_id,
                        'error': e,
                        'message_code': 'ERROR_ENQUEING_INVOICE',
                    }
                )


            return HttpResponseRedirect(reverse('tresorerie:historique'))

        else:
            ERRORS = {
                'requires_source': _("Le paiement n'a pas été effectué"),
                'requires_payment_method': _("Le paiement n'a pas été effectué"),
                'requires_confirmation': _("Le paiement n'a pas été confirmé"),
                'requires_source_action': _("Le paiement n'a pas été authentifié"),
                'requires_action': _("Le paiement n'a pas été authentifié"),
                'processing': _("Le paiement est en attente. Veuillez contacter un administrateur dans une heure."),
                'requires_capture': _("Une erreur est survenue. Veuillez contacter un administrateur."),
                'canceled': _("Le paiement a été annulé"),
            }

            logger.error(
                "Paiement échoué, erreur : %s, uid : %s" % (payment_status,
                                                            request.ldap_user.uid),
                extra={
                    "error_code": payment_status,
                    "uid": request.ldap_user.uid,
                    'message_code': 'STRIPE_PAYMENT_ERROR',
                }
            )
            messages.error(request, ERRORS[payment_status])
            return HttpResponseRedirect(reverse('tresorerie:pay', kwargs={'product_id': main_product_id}))


class History(ListView):
    """
    This view show to the user the history of his payments
    """

    template_name = 'tresorerie/history.html'
    context_object_name = 'transactions'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(History, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Transaction.objects.all().filter(utilisateur__exact=self.request.user).order_by('date_creation')


@method_decorator(login_required, name="dispatch")
class TransactionDetailView(DetailView):

    model = Transaction
    template_name = "tresorerie/transaction_detail.html"
    slug_field = "uuid"

    def get_object(self, queryset=None):
        transaction = super(TransactionDetailView, self).get_object(queryset)

        if transaction.utilisateur != self.request.ldap_user.uid:
            # 404 because the user should not even know if the object exists
            raise Http404(_("Aucune transaction trouvée"))
        return transaction

    def get_context_data(self, **kwargs):
        context = super(TransactionDetailView, self).get_context_data(**kwargs)
        context['user'] = self.request.ldap_user
        context['main_product'] = context['transaction'].produit.all()[0]
        context['products'] = context['transaction'].produit.all()

        # Get invoice
        filename = os.path.join(settings.MEDIA_ROOT, settings.INVOICE_STORE_PATH,
                                "{}-{}.pdf".format(
                                    self.request.ldap_user.uid,
                                    str(context['transaction'].uuid)
                                ))

        if os.path.isfile(filename):
            context['invoice_path'] = os.path.relpath(filename, settings.MEDIA_ROOT)

        else:
            context['invoice_path'] = None

            # Trigger invoice regeneration
            user_data = {
                'first_name': self.request.ldap_user.first_name,
                'last_name' : self.request.ldap_user.last_name,
                'uid': self.request.ldap_user.uid,
                'email' : self.request.ldap_user.mail,
                'address' : self.request.ldap_user.postal_address,
            }
            transaction_data = {
                'uuid': context['transaction'].uuid,
                'date_creation': context['transaction'].date_creation,
                'date_paiement': context['transaction'].date_creation,
                'statut': context['transaction'].statut,
                'moyen': context['transaction'].get_moyen_display(),
                'total': context['transaction'].total,
                'admin': context['transaction'].admin,
                'categories': [
                    {'name': cat, 'products': prods} for cat, prods in context['transaction'].get_products_by_cat()
                ],
            }
            user_lang = get_language().split('-')[0]
            queue = django_rq.get_queue()
            queue.enqueue_call(
                async_tasks.generate_and_email_invoice,
                args=(user_data, transaction_data, user_lang, 'user'),
            )

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

        products_FIG = list(Product.objects.filter(type_produit="F", autorisation="FIG"))
        products_FIG += list(Product.objects.filter(type_produit="F", autorisation="ALL"))
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
