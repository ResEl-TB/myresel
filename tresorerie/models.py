from django.db import models
from django.utils import timezone

class Transaction(models.Model):
    """ Model used to save a transaction made with the user """

    utilisateur = models.CharField(max_length=50)
    moyen = models.CharField(default='CB', max_length=2)
    date = models.DateField(auto_now_add=True)
    admin = models.CharField(max_length=100, null=True, blank=True)
    total = models.FloatField()
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.utilisateur, self.commentaire)

class MonthlyPayment(models.Model):
    """ Model used to say if the user is doing monthly payments """

    class META:
        verbose_name = "paiement mensuel"
        verbose_name_plural = "paiements mensuels"

    user = models.CharField(max_length = 50)
    months_to_pay = models.IntegerField()
    months_paid = models.IntegerField(default = 0)
    customer = models.CharField(max_length=50)
    last_paid = models.DateField(default=timezone.now())
    amount_to_pay = models.FloatField()

    def __str__(self):
        return "%s - Payment %d/%d" % (self.user, self.months_paid, self.months_to_pay)
