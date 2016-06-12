my.resel.fr
===========

Paquets à installer
-------------------
- django

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
- internationalisation

Pense-bête
==========
- prendre en compte les messages (error, success, info, etc.) sur le template de la page de news (page de base, sur laquelle tout est redirigé)
- prise en compte de ces messages aussi sur la page Home
- dans la page d'ajout, checker en javascript si l'alias de la machine est valide et disponible
- dans la page d'ajout d'une personne, check en javascript si le pseudo choisi est valide et dispo
- dans la page de demande d'ajout de machine, vérifier que la MAC est valide en javascript