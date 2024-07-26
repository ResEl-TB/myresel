Le site resel.fr
================

[![build status](https://git.resel.fr/resel/applications-utilisateurs/myresel/badges/master/build.svg)](https://git.resel.fr/resel/applications-utilisateurs/myresel/commits/master)
[![coverage report](https://git.resel.fr/resel/applications-utilisateurs/myresel/badges/master/coverage.svg)](https://git.resel.fr/resel/applications-utilisateurs/myresel/commits/master)


Ceci est le code pour le site ResEl [resel.fr](resel.fr) il est développé en
[Python](https://python.org) avec le [framework
Django](https://www.djangoproject.com/). Ce document a pour objectif de vous
présenter rapidement le projet et son fonctionnement. Il sert également de
guide pour les nouveaux développeurs qui veulent contribuer au projet et de
guide pour les administrateurs systèmes qui voudraient installer (ou réparer)
le service.

Dans la suite du document nous supposons que le lecteur est famillier avec
[Python](https://python.org) et avec le framework
[Django](https://www.djangoproject.com/) (et toutes les technologies associées
HTTP, MYSQL, HTML, CSS, Javascript).

![](.gitlab/screen1.png)

# Démarrage en 2 minutes
Cette démarche vous permettra d'avoir un serveur de développement prêt à être
utilisé en créant et en populant les bases de données (MYSQL, LDAP)
automatiquement. Nous utilisons Vagrant qui permet de faire tout cela
automagiquement.

Installer [Vagrant](https://www.vagrantup.com/)
```
sudo apt install vagrant  # On a Debian-based distribution
```

Installer l'environement de développement :
```
git clone https://git.resel.fr/resel/applications-utilisateurs/myresel
cd myresel/
vagrant up  # It might take a while the first time
```

Démarrer le serveur :
```
vagrant ssh
cd /myresel
python3 manage.py rqworker default &
python3 manage.py rqscheduler default &
python3 manage.py runserver 0.0.0.0:8000
```

Sur votre navigateur web rendez-vous sur :
 - `http://10.0.3.94:8000` Simule le VLAN 994 (extérieur)
 - `http://10.0.3.95:8000` Simule le VLAN 995 (réseau d'inscription)
 - `http://10.0.3.99:8000` Simule le VLAN 999 (machine inscrite)
 - `http://10.0.3.199:8000` Simule le VLAN 999 (machine non inscrite)

Votre adresse MAC sera par défaut : "0a:00:27:00:00:10", Vous pouvez la changer
dans le fichier `myresel/settings_local.py`.

# Documentation
# -> Voir [/doc](doc/README.md)

**j'ai mis en gros, c'est pas pour rien ;-).**

-------------------------------------------------------------------------------

# Faire un hotfix/modification sur les serveurs de prod

#### :warning: Contrairement à 99% des autres services ResEl vous ne devez quasiment en **aucun cas toucher aux serveurs de production**. Voici la procédure :
 
Clonez le repo sur votre ordinateur :
```bash
git clone https://git.resel.fr/resel/applications-utilisateurs/myresel
```

Faites les modifications nécessaires dans le repo. Si les modifications que
vous souhaitez executer ne sont pas triviales je vous recommande de faire une
branche :
```bash
git checkout -b branch_name
```

Vous pouvez ensuite effectuer vos modifications puis pusher la branche sur
Gitlab 
```
git push --set-upstream branch_name
```

Ou alors plus simplement si vous n'avez pas créé de branche : `git push`

Si vous avez créé une branche n'oubliez pas de [créer une merge request depuis
votre branche vers `master`](https://git.resel.fr/resel/applications-utilisateurs/myresel/merge_requests/new?merge_request%5Btarget_branch%5D=master).
Et demandez à faire un code review ! Puis mergez la branche.

Il faut ensuite pusher le code en production, pour ceci il suffit de [créer une
merge request de `master` vers `deploy`](https://git.resel.fr/resel/applications-utilisateurs/myresel/merge_requests/new?utf8=✓&merge_request[source_branch]=master&merge_request[target_branch]=deploy)
à la suite de quoi, si les tests passent, le code sera automatiquement pushé
sur les serveurs de production.


# Zone d'inscription

Du fait de l'architecture très spécialisée du ResEl, toute les fonctionnalités
touchants à l'inscription et la gestion des machines sont sensibles. En effet,
pour détecter la bonne addresse MAC et pour proposer un site différent
dépendant de l'origine de l'utilisateur, il est nécéssaire de mettre la machine
sur plusieurs réseaux.  

Dépendant du VLAN d'origine, le serveur NGINX taggera les requêtes HTTP
différement. Puis, en fonction du tag les middlewares `NetworkConfiguration` et
`InscriptionNetworkHandler` ajouterons des métadonnées aux requetes (comme par
exemple l'adresse mac de l'utilisateur) puis vont rerouter les requêtes vers
les bonnes vues.

Dans l'environnement de développement, comme il est extrêmement compliqué de
totalement simuler l'architecture du ResEl, le choix a été fait de créer un
nouveau middleware `SimulateProductionNetwork` qui empoisonera les requetes
avec de fausses ip.


# Astuces

## Mettre le site en mode maintenance

Lorsque vous avez de grosses migrations à faire, il est parfois nécéssaire de
mettre le site en mode maintenance pour éviter que les utilisateurs écrivent
dans la base de données en même temps que vos migrations. Pour cela il suffit
de renommer le fichier `maintenance_off.html` en `maintenance_on.html`. Si la
configuration de nginx est correcte, le site devrait retourner une erreur `503`
le temps de faire la migration. 

```bash
# Activer la maintenance
mv maintenance_off.html maintenance_on.html

# Désactiver la maintenance
mv mv maintenance_on.html maintenance_off.html
```


## Passer superutilisateur sur l'environement de dev

Pour pouvoir administrer le site il faut avoir un compte avec les droits
admins.  Malheureusement en local (comme la population de la base de données
n'est pas encore terminée) il n'est pas facile de se créer un compte admin.
Voici un petit hack que je vous propose :


1. Modifier le ficher `myresel/middleware.py`, à la ligne 30 remplacer :
    ```python
    if res:
        user = User.objects.get(username=request.user.username)
    ```
    
    par :
    ```python
    if True:
        user = User.objects.get(username=request.user.username)
    ```

2. Démarrer le serveur 
    ```bash
    python3 manage.py runserver 0.0.0.0:8000
    ```
2. Créer un compte avec le site en se rendant sur l'adresse suivante : 
   http://10.0.3.99:8000/personnes/inscription

Vous pouvez vous connecter à l'administration en cliquant sur les engrenages
dans la barre de navigation.

# Notes

Deux modules : la génération automatique de facture et l'affichage des
documents de l'association, reposent sur un service
[LaPuTeX](https://git.resel.fr/resel/applications-admins/LaPuTeX).  Pour mettre le mettre en
place, suivez les détails du [README](https://git.resel.fr/resel/applications-admins/LaPuTeX) puis
configurer le `settings_local.py` ou bien utilisez l'installateur automatique :

```python
LAPUTEX_HOST = "http://10.0.3.253:8000/"
LAPUTEX_DOC_URL = LAPUTEX_HOST+"beta/documents/"
LAPUTEX_TOKEN = "test"
```

Ceci peut être fait automatiquement en lancant la deuxième VM :
```bash
vagrant up laputex
vagrant ssh laputex

celery worker -A laputex.celery --loglevel=debug &
python3 -m laputex
```

Bugs connu : 
 * La facture générée automatiquement ne peut pas gérer des prix supérieurs à 1 million 70 mille €.
 
-----------------------

# Crédits
Pour ce magnifique site, on peut remercier : 
 - Loïc Carr @dimtion : loic.carr@telecom-bretagne.eu
 - Jean-Baptiste Valladeau @jbvalladeau : jean-baptiste.valladeau@telecom-bretagne.eu
 - Théo Jacquin @nimag42 : theo.jacquin@telecom-bretagne.eu
 - Guillaume Buret @thebigtouffe : guillaume.buret@telecom-bretagne.eu
 - Morgan Robin @tharkunn : morgan.robin@telecom-bretagne.eu

Code sous license [GPL](LICENSE)

Allez lire la [documentation](doc/README.md) !
