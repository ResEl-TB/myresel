# -*- coding: utf-8 -*-
"""
Version 2 of the tresorerie module.
The database should be enough to make stripe payment work now
"""

import uuid

import django
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Bank(models.Model):
    """
    Model used to store a bank into the database
    """
    class Meta:
        verbose_name = 'banque'

    nom = models.CharField(
        max_length=100,
    )

    def __str__(self):
        return self.nom


class Check(models.Model):
    """
    Model used to keep track of a check in the database
    """
    class Meta:
        verbose_name = 'chèque'

    banque = models.ForeignKey(
        'Bank',
        on_delete=models.CASCADE,
    )

    numero = models.IntegerField(
        verbose_name='numéro',
    )

    nom = models.CharField(
        max_length=100,
    )

    date_emission = models.DateField(
        auto_now_add=True,
        verbose_name='date d\'émission',
    )

    montant = models.FloatField()

    encaisse = models.BooleanField(
        default=False,
        editable=False,
        verbose_name='encaissé',
    )

    date_encaissement = models.DateField(
        null=True,
        blank=True,
    )

    transaction = models.ForeignKey(
        'Transaction',
        on_delete=models.DO_NOTHING,
    )

    def __str__(self):
        return '%.2f € - %s' % (self.montant, self.nom)


class Product(models.Model):
    """
    Model used to describe all the products we sell
    """
    class Meta:
        verbose_name = 'produit'

    TYPES_PRODUITS = (
        ('A', 'Adhésion'),
        ('M', 'Matériel'),
        ('F', 'Frais d\'accès'),
    )

    AUTH = (
        ('FIG', 'FIG'),
        ('FIP', 'FIP'),
        ('ALL', 'ALL'),
    )

    nom = models.CharField(
        max_length=100,
    )

    prix = models.IntegerField()

    type_produit = models.CharField(
        max_length=1,
        verbose_name='type de produit',
        choices=TYPES_PRODUITS,
    )

    duree = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(12),
        ],
        help_text='Durée en mois des frais d\'accès (si type = frais d\'accès, laisser vide sinon)',
        verbose_name='durée',
        blank=True,
    )

    autorisation = models.CharField(
        max_length=3,
        verbose_name='Authorisation d\'achat',
        help_text='Définit qui est éligible à ce produit',
        choices=AUTH,
        default='ALL',
    )

    @property
    def display_price(self):
        return self.prix / 100

    def __str__(self):
        return '%s %.2f €' % (self.nom, self.prix / 100)


class Transaction(models.Model):
    """
    Model used to save a transaction made with the user
    """

    STATUTS = (
        ('A', 'En attente'),
        ('N', 'Non payée'),
        ('P', 'Payée'),
        ('E', 'Erreur'),
    )

    uuid = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
    )

    MOYENS_PAY = (
        ('L', 'Liquide'),
        ('C', 'Chèque'),
        ('CB', 'Carte bancaire'),
    )

    utilisateur = models.CharField(
        max_length=50,
        blank=True,
    )

    moyen = models.CharField(
        max_length=2,
        verbose_name='moyen de paiement',
        choices=MOYENS_PAY,
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
    )

    produit = models.ManyToManyField(
        'Product',
    )

    admin = models.CharField(
        max_length=100,
    )

    commentaire = models.TextField(
        blank=True,
        null=True,
    )

    total = models.FloatField(
        default=0,
    )

    stripe_id = models.CharField(
        blank=True,
        null=True,
        max_length=30,
        unique=True,
    )

    statut = models.CharField(
        verbose_name='Statut de la transaction',
        choices=STATUTS,
        max_length=3,
        default='N',
    )

    date_paiement = models.DateTimeField(
        null=True,
        blank=True,
    )

    facture = models.CharField(
        verbose_name="Chemin de la facture en pdf",
        max_length=500,
        null=True,
        blank=True,
    )

    def __str__(self):
        return 'Transaction du %s de l\'utilisateur %s' % (self.date_creation, self.utilisateur)

    def get_checks(self):
        return Check.objects.all().filter(transaction=self.pk)

    def get_products_by_cat(self):
        products_by_cat = []

        for c_id, c in Product.TYPES_PRODUITS:
            products = [p for p in list(self.produit.all()) if p.type_produit == c_id]
            if len(products) > 0:
                products_by_cat.append((c, products))

        return products_by_cat

    def get_main_product(self):
        return self.produit.order_by('-prix')[0]


class MonthlyPayment(models.Model):
    """ Model used to say if the user is doing monthly payments """

    class Meta:
        verbose_name = "paiement mensuel"
        verbose_name_plural = "paiements mensuels"

    user = models.CharField(max_length=50)
    months_to_pay = models.IntegerField()
    months_paid = models.IntegerField(default=0)
    customer = models.CharField(max_length=50)
    last_paid = models.DateField(default=django.utils.timezone.now)
    amount_to_pay = models.FloatField()

    def __str__(self):
        return "%s - Payment %d/%d" % (self.user, self.months_paid, self.months_to_pay)


class StripeCustomer(models.Model):
    """
    A model to make the link between stripe customers and LdapUsers
    """

    ldap_id = models.CharField(max_length=50, primary_key=True)
    stripe_id = models.CharField(max_length=50, unique=True)

    @staticmethod
    def retrieve_or_create(user):
        import stripe
        try:
            customer_id = StripeCustomer.objects.get(ldap_id=user.uid).stripe_id
            return stripe.Customer.retrieve(customer_id)
        except ObjectDoesNotExist:
            desc = "%s : %s %s " % (
                user.uid,
                user.first_name,
                user.last_name.upper(),
            )

            customer = stripe.Customer.create(
                description=desc,
                email=user.mail,
                metadata={'uid': user.uid},
            )

            db_cus = StripeCustomer()
            db_cus.ldap_id = user.uid
            db_cus.stripe_id = customer.id
            db_cus.save()

            return customer
