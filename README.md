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
- page 404
- page 500
- contact
- myresel :
    - news
    - home
- gestion-machines :
    - reactivation
    - changement de campus
    - inscription machine
- gestion-personnes :
    - inscription dans le LDAP
- tresorerie :
    - historique des transactions de l'user
    - paiement en ligne de la cotiz
- internationalisation

Pense-bête
==========
- prendre en compte les messages (error, success, info, etc.) sur le template de la page de news (page de base, sur laquelle tout est redirigé)
- prise en compte de ces messages aussi sur la page Home
- dans la page d'ajout, checker en javascript si l'alias de la machine est valide et disponible
- dans la page d'ajout d'une personne, check en javascript si le pseudo choisi est valide et dispo
- dans la page de demande d'ajout de machine, vérifier que la MAC est valide en javascript
- système de questions déroulantes en javascript pour le montant de la cotiz à payer
- script qui gère le paiement auto des autres mensualisations
- générer des factures pour les paiements
