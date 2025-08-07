# -*- coding: utf-8 -*-
import uuid
import os
from datetime import datetime
from urllib.parse import quote_plus
import logging
import json
from dateutil.relativedelta import relativedelta

import django_rq
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _, get_language
from django.views.generic import DetailView, View, ListView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from tresorerie import async_tasks
from fonctions import generic
from fonctions.decorators import need_to_pay, able_to_pay, not_maisel
from tresorerie.models import Transaction, Product, StripeCustomer
from gestion_personnes.models import LdapUser

logger = logging.getLogger("default")


class ChooseProduct(View):
    """
    Page to choose a product from
    """

    template_name = 'tresorerie/choose_product.html'

    @method_decorator(login_required)
    @method_decorator(able_to_pay)
    @method_decorator(need_to_pay)
    @method_decorator(not_maisel)
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
    @method_decorator(not_maisel)
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
            metadata={ # User info for the new webhook processing
                'transaction_uuid': str(transaction.uuid),
                'user_uid': request.ldap_user.uid,
                'products_ids': ','.join(str(p.id) for p in products),
                
                'user_first_name': request.ldap_user.first_name,
                'user_last_name': request.ldap_user.last_name,
                'user_email': request.ldap_user.mail,
                'user_address': request.ldap_user.postal_address,
            }
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
        """Triggered when the user submits the payment form, main logic moved to webhooks"""
        user = request.ldap_user
        
        try:
            given_uuid = uuid.UUID(request.POST['uuid'])
            session_uuid = uuid.UUID(request.session['transaction_uuid'])
        except (MultiValueDictKeyError, ValueError, KeyError):
            messages.error(request, _("Payment validation error."))
            return HttpResponseRedirect(reverse('tresorerie:choose-product'))
        
        if given_uuid != session_uuid:
            messages.error(request, _("Payment validation error."))
            return HttpResponseRedirect(reverse('tresorerie:choose-product'))
        
        # Verify that the PaymentIntent exists and belongs to us
        try:
            payment_intent = stripe.PaymentIntent.retrieve(request.session['payment_intent'])
            if payment_intent.metadata.get('user_uid') != user.uid:
                messages.error(request, _("Security error detected."))
                return HttpResponseRedirect(reverse('tresorerie:choose-product'))
        except stripe.error.InvalidRequestError:
            messages.error(request, _("Invalid payment."))
            return HttpResponseRedirect(reverse('tresorerie:choose-product'))
        
        # if we don't detect any message, we assume the payment is being processed
        messages.info(request, _(
            "Your payment is being processed. "
            "You will receive a confirmation email within a few minutes."
        ))
        
        logger.info(
            f"Payment submitted: uid={user.uid}, uuid={session_uuid}",
            extra={
                'uid': user.uid,
                'transaction_uuid': str(session_uuid),
                'message_code': 'PAYMENT_SUBMITTED'
            }
        )
        
        return HttpResponseRedirect(reverse('tresorerie:historique'))

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


@method_decorator(csrf_exempt, name='dispatch') # this is an api so we don't want CSRF (im not CSRF-ist I promise)
@method_decorator(require_POST, name='dispatch')
class StripeWebhookView(View):
    """
    Stripe webhook handler to improve payment security & reliability
    """
    
    def dispatch(self, *args, **kwargs):
        return super(StripeWebhookView, self).dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle Stripe webhook events"""

        # check signature
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Webhook invalid payload: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook invalid signature: {e}")
            return HttpResponse(status=400)
        
        # Process events
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            try:
                with transaction.atomic():
                    self.process_successful_payment(payment_intent)
            except ValueError as e:
                # Client errors (invalid data) - don't retry
                logger.error(
                    f"Webhook validation error: {e}",
                    extra={
                        'stripe_payment_intent': payment_intent.id,
                        'payment_intent_metadata': payment_intent.metadata,
                        'message_code': 'WEBHOOK_VALIDATION_ERROR'
                    }
                )
                return HttpResponse(status=400)
            except Exception as e:
                # Server errors (LDAP down, DB issues) - retry
                logger.error(
                    f"Webhook processing error: {e}",
                    extra={
                        'stripe_payment_intent': payment_intent.id,
                        'payment_intent_metadata': payment_intent.metadata,
                        'message_code': 'WEBHOOK_PROCESSING_ERROR'
                    }
                )
                return HttpResponse(status=500)
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            logger.warning(
                f"Payment failed via webhook: {payment_intent.id}",
                extra={'stripe_payment_intent': payment_intent.id}
            )
        
        return HttpResponse(status=200)
    
    def process_successful_payment(self, payment_intent):
        """Process a successful payment via webhook"""
        
        # Retrieve metadata
        metadata = payment_intent.metadata
        transaction_uuid = uuid.UUID(metadata.get('transaction_uuid'))
        user_uid = metadata.get('user_uid')
        products_ids = [int(pid) for pid in metadata.get('products_ids', '').split(',') if pid]
        
        # Basic validation
        if not all([transaction_uuid, user_uid, products_ids]):
            raise ValueError("Incomplete metadata in PaymentIntent")
   

        # Check if this Stripe payment id has already been processed, we don't like replay attacks here sorry
        existing_stripe_transaction = Transaction.objects.filter(stripe_id=payment_intent.id).first()
        if existing_stripe_transaction:
            logger.warning(
                f"Stripe payment {payment_intent.id} already processed for transaction {existing_stripe_transaction.uuid}",
                extra={
                    'stripe_payment_intent': payment_intent.id,
                    'existing_transaction_uuid': str(existing_stripe_transaction.uuid),
                    'new_transaction_uuid': str(transaction_uuid),
                    'message_code': 'WEBHOOK_DUPLICATE_STRIPE_ID'
                }
            )
            return  



        # Idempotent transaction uuid check
        transaction_obj, created = Transaction.objects.get_or_create(
            uuid=transaction_uuid,
            defaults={
                'moyen': "CB",
                'utilisateur': user_uid,
                'total': payment_intent.amount / 100,
                'stripe_id': payment_intent.id,
            }
        )
        
        if not created:
            logger.info(f"Transaction {transaction_uuid} already processed via webhook")
            return  
        
        # Retrieve objects
        try:
            products = Product.objects.filter(id__in=products_ids)
        except Exception as e:
            raise ValueError(f"Products not found: {e}")
    
  
        
        # This is to ensure that the amount matches the products selected
        expected_amount = sum(p.prix for p in products)
        if payment_intent.amount != expected_amount:
            raise ValueError(
                f"Amount mismatch: received {payment_intent.amount}, "
                f"expected {expected_amount}"
            )
        
        
        # Add products to transaction
        for product in products:
            transaction_obj.produit.add(product)
        transaction_obj.save()

        # Get user from LDAP
        try:
            user = LdapUser.get(uid=user_uid)
            if not user:
                # This is likely a temporary LDAP issue or potential security issue
                raise Exception(f"User {user_uid} not found in LDAP - could be LDAP connectivity issue or invalid user")
        except Exception as e:
            logger.error(
                f"LDAP user retrieval failed: {e}",
                extra={
                    'uid': user_uid,
                    'transaction_uuid': str(transaction_uuid),
                    'stripe_payment_intent': payment_intent.id,
                    'ldap_error_type': type(e).__name__,
                    'message_code': 'WEBHOOK_LDAP_USER_ERROR'
                }
            )
            # Re-raise to trigger webhook retry
            raise Exception(f"LDAP user retrieval failed for {user_uid}: {e}") 
        

        # Update user (login remained unchanged from previous system)
        adhere = any(p.type_produit == 'A' for p in products)
        if adhere:
            year = generic.current_year()
            user.cotiz = [c for c in user.cotiz if c.lower() != f"none{year}"] + [str(year)]
        
        month_numbers = sum(p.duree for p in products if p.type_produit == 'F')
        if month_numbers > 0:
            if user.end_cotiz is None:
                user.end_cotiz = datetime.now().astimezone()
            start = max(user.end_cotiz, datetime.now().astimezone())
            user.end_cotiz = start + relativedelta(months=month_numbers)
        
        user.save()
    

        
        # Generate invoice asynchronously
        self.enqueue_invoice_generation(user, transaction_obj)
        
        logger.info(
            f"Payment processed successfully via webhook: {user_uid}, {transaction_uuid}",
            extra={
                'uid': user_uid,
                'transaction_uuid': str(transaction_uuid),
                'transaction_stripe_id': payment_intent.id,
                'message_code': 'WEBHOOK_PAYMENT_SUCCESS'
            }
        )
    
    def enqueue_invoice_generation(self, user, transaction_obj):
        """Generate invoice in queue"""
        user_datas = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'uid': user.uid,
            'email': user.mail,
            'address': user.postal_address,
        }
        transaction_datas = {
            'uuid': transaction_obj.uuid,
            'date_creation': transaction_obj.date_creation,
            'date_paiement': transaction_obj.date_creation,
            'statut': transaction_obj.statut,
            'moyen': transaction_obj.get_moyen_display(),
            'total': transaction_obj.total,
            'admin': transaction_obj.admin,
            'categories': [
                {'name': cat, 'products': prods} 
                for cat, prods in transaction_obj.get_products_by_cat()
            ],
        }
        
        try:
            queue = django_rq.get_queue()
            queue.enqueue_call(
                async_tasks.generate_and_email_invoice,
                args=(user_datas, transaction_datas, 'fr', 'user-treasurer'),
            )
        except Exception as e:
            logger.error(f"Invoice generation error: {e}")



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
