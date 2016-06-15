my.resel.fr
===========

Environnement de travail
------------------------

Définir un environnement virtuel python, avec python3.

```
pip3 install virtualenv
virtualenv -p python3 .
source bin/activate
```

Paquets à installer
-------------------
- django
- stripe
- ldap

```
pip3 -r requirements.txt
```

Mise en marche
--------------

```
./manage.py runserver
```

Se connecter ensuite en localhost:8000 pour visualiser

--> enjoy !

TODO
====
- paiement
- gestion du compte MyResEl de l'utilisateur
- [OK] page 400
- [OK] page 403
- [OK] page 404
- [OK] page 500
- [OK] contact
- myresel :
    - [OK] news
    - [OK] home
- gestion-machines :
    - [OK] ré-activation
    - [OK] changement de campus
    - [OK] inscription machine
- gestion-personnes :
    - inscription dans le LDAP
- trésorerie :
    - historique des transactions de l'user
    - paiement en ligne de la cotiz
- internationalisation

Pense-bête
==========
- [OK] prendre en compte les messages (error, success, info, etc.) sur le template de la page de news (page de base, sur laquelle tout est redirigé)
- [OK] lors d'une erreur de validation du formulaire, afficher l'erreur à l'utilisateur pour lui dire quoi changer
- dans la page d'ajout d'une personne, check en javascript si le pseudo choisi est valide et dispo
- [OK] dans la page de demande d'ajout de machine, vérifier que la MAC est valide en javascript
- système de questions déroulantes en javascript pour le montant de la cotiz à payer
- script qui gère le paiement auto des autres mensualisations
- générer des factures pour les paiements
