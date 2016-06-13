from django.db import models

# Create your models here.
class Produit(models.Model):
    """ Modèle pour la gestion des stocks sur les produits que l'on vend, ici une cotisation """

    nom = models.CharField()
    prix = models.FloatField()

class Transaction(models.Model):
    """ Modèle pour la gestion des transactions réalisées """

    utilisateur = models.CharField()
    moyen = models.CharField(default = 'CB')
    date = models.DateField(auto_now_add = True)
    produit = models.ManyToManyField(Produit)
    total = models.FloatField()
    commentaire = models.TextField(blank = True, null = True)

    def __init__(self, user, montant):
        super().__init__()
        self.utilisateur = models.CharField(default = user)
        self.total = models.FloatField(default = montant)