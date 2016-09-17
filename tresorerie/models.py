from datetime import date

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


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
        default=date.today(),
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
    )

    def __str__(self):
        return '%.2f € - %s' % (self.montant, self.nom)


class Product(models.Model):
    """
    Model used to describe all the products we sell
    """
    class Meta:
        verbose_name = 'produit'

    TYPES = (
        ('A', 'Adhésion'),
        ('M', 'Matériel'),
        ('F', 'Frais d\'accès'),
    )

    nom = models.CharField(
        max_length=100,
    )

    prix = models.FloatField()

    type_produit = models.CharField(
        max_length=1,
        verbose_name='type de produit',
        choices=TYPES,
    )

    duree = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(12),
        ],
        help_text='durée en mois des frais d\'accès (si type = frais d\'accès, laisser vide sinon)',
        verbose_name='durée',
        blank=True,
    )

    def __str__(self):
        return '%s - %.2f €' % (self.nom, self.prix)


class Transaction(models.Model):
    """
    Model used to save a transaction made with the user
    """

    CHOICES = (
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
        choices=CHOICES,
    )

    date = models.DateField(
        auto_now_add=True,
    )

    produit = models.ManyToManyField(
        'Product',
        null=True,
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

    def __str__(self):
        return 'Transaction du %s de l\'utilisateur %s' % (self.date, self.utilisateur)

    def get_checks(self):
        return Check.objects.all().filter(transaction=self.pk)


class MonthlyPayment(models.Model):
    """ Model used to say if the user is doing monthly payments """

    class Meta:
        verbose_name = "paiement mensuel"
        verbose_name_plural = "paiements mensuels"

    user = models.CharField(max_length=50)
    months_to_pay = models.IntegerField()
    months_paid = models.IntegerField(default=0)
    customer = models.CharField(max_length=50)
    last_paid = models.DateField(default=timezone.now)
    amount_to_pay = models.FloatField()

    def __str__(self):
        return "%s - Payment %d/%d" % (self.user, self.months_paid, self.months_to_pay)
