from django.db import models

# Create your models here.
class Produit(models.Model):
    """ Modèle pour la gestion des stocks sur les produits que l'on vend, ici une cotisation """

    nom = models.CharField(max_length = 50)
    prix = models.FloatField()

class Transaction(models.Model):
    """ Modèle pour la gestion des transactions réalisées """

    utilisateur = models.CharField(max_length = 50)
    moyen = models.CharField(default = 'CB', max_length = 2)
    date = models.DateField(auto_now_add = True)
    produit = models.ManyToManyField(Produit)
    total = models.FloatField()
    commentaire = models.TextField(blank = True, null = True)

class Mensualisation(models.Model):
    """ Modèle pour la gestion de la mensualisation """

    utilisateur = models.CharField(max_length = 50)
    nb_m = models.IntegerField() # Nombre de mensualités à payer
    nb_p = models.IntegerField(default = 0) # Nombre de mensualités payées
    customer = models.IntegerField() # ID de l'objet customer associé à l'utilisateur