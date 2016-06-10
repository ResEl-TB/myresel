from django.shortcuts import render
from django.views.generic import TemplateView
from fonctions import ldap

# Pour la traduction - sert à marquer les chaînes de caractères à traduire
from django.utils.translation import ugettext_lazy as _

# Create your views here.
class Inscription(TemplateView):
    """
    Vue appelée pour que l'user s'inscrive au ResEl
    C'est cette vue qui créer la fiche LDAP de l'user
    On lui affiche le réglement intérieur, et un formulaire pour remplir les champs LDAP
    """

    rech = ldap.search("ou=people,dc=maisel,dc=enst-bretagne,dc=fr" , "(&(uid=%s))" % self.request.user)
    if len(rech) != 0:
        # L'utilisateur est déjà présent dans le LDAP, on le redirige sur une page d'erreur
        pass

    # On ajoute l'utilisateur