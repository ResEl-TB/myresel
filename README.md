my.resel.fr
===========


## Quick startup

Install [Vagrant](https://www.vagrantup.com/)
```
sudo apt install vagrant  # On a Debian installation
```

Install the dev environment :
````
git clone ...
cd myresel/
vagrant up  # It might take a while, thanks to the LaTeX environment :p
````

Launch the server :
````
vagrant ssh
cd /myresel
python3 manage.py rqworker default &
python3 manage.py runserver 0.0.0.0:8000
````

Then launch your web browser to :
 - `http://10.0.3.94:8000` to simulate the 994 VLAN (from the exterior)
 - `http://10.0.3.95:8000` to simulate the 995 VLAN (from the open Wi-Fi)
 - `http://10.0.3.99:8000` to simulate the 999 VLAN (with a known machine)
 - `http://10.0.3.199:8000` to simulate the 999 VLAN (with an unknown machine)

Your mac address will always be : "0a:00:27:00:00:10", You can change it in the `settings_local.py` file


## TODO

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
- [OK] générer des factures pour les paiements
