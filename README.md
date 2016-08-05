my.resel.fr
===========


Quick setup
-------------
Install [Vagrant](https://www.vagrantup.com/)
```
sudo apt install vagrant
```

Install the dev environment :
````
git clone ...
cd myresel/
cp myresel/credentials.py.tpl myresel/credentials.py
vagrant up  # It might take a while, thanks to the LaTeX environment
````

Launch the server :
````
vagrant ssh
cd /
python3 runserver 0.0.0.0:8000
````

Then launch your web browser to : `127.0.0.1:8000`

Done.


If you don't like vagrant, follow the manual method :

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

### Paquets système :

- python3
- texlive-latex-extra
- redis-server

```
apt install python3 texlive-latex-extra redis-server
```

### Paquets python :

- django
- stripe
- ldap

```
pip3 -r requirements.txt
```

Mise en marche
--------------

Faire un pull sur Skynet, et go sur https://my.resel.fr

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
    - [A tester] inscription dans le LDAP
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
- [OK] système de questions déroulantes en javascript pour le montant de la cotiz à payer
- script qui gère le paiement auto des autres mensualisations
- [PARTIAL] générer des factures pour les paiements
