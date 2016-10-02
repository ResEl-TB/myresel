Le site resel.fr
================

Ceci est le code pour le nouveau site ResEl [resel.fr](resel.fr) il est développé en [Python](https://python.org) avec le framework [Django](https://www.djangoproject.com/). Ce document a pour objectif de vous présenter rapidement le projet et son fonctionnement. Il sert également de guide pour les nouveaux développeurs qui veulent contribuer au projet et de guide pour les administrateurs systèmes qui voudraient installer (ou réparer) le service.

Dans la suite du document nous supposons que le lecteur est famillier avec [Python](https://python.org) et avec le framework [Django](https://www.djangoproject.com/) (et toutes les technologies associées HTTP, MYSQL, HTML, CSS, Javascript).

![](.gitlab/screen1.png)

## Sommaire
 - [Démarrage en 2 minutes](#démarrage-en-2-minutes)
 - [Tests](#tests)
 - [Liste des modules](#liste-des-modules)
   - [Modules](#modules)
   - [Autres dossiers](#autres-dossiers)
 - [Conventions et bonnes pratiques](#conventions-et-bonnes-pratiques)
 - [Environment de production](#environment-de-production)
   - [Configuration matérielle](#configuration-matérielle)
   - [Configuration du DNS et du DHCP](#configuration-du-dns-et-du-dhcp)
   - [Exceptions au Firewall](#exceptions-au-firewall)
   - [Installation de base](#installation-de-base)
   - [Configuration de nginx](#configuration-de-nginx)
   - [Configuration de uwsgi](#configuration-de-uwsgi)
   - [Configuration de Supervisor](configuration-de-supervisor)
   - [Configuration du site](#configuration-du-site)
   - [Lancement du service](#lancement-du-service)
   - [Monitoring](#monitoring)
   - [Notes](#notes)
 - [Astuces](#astuces)
 - [Crédits](#crédits)
   
 
   
## Démarrage en 2 minutes
Cette démarche vous permettra d'avoir un serveur de développement prêt à être utilisé en créant et en populant les bases de données (MYSQL, LDAP) automatiquement. Nous utilisons Vagrant qui permet de faire tout cela automagiquement.

Installer [Vagrant](https://www.vagrantup.com/)
```
sudo apt install vagrant  # On a Debian installation
```

Installer l'environement de developpement :
````
git clone https://git.resel.fr/resel/myresel
cd myresel/
vagrant up  # It might take a while, thanks to the LaTeX environment :p
````

Démarrer le serveur :
````
vagrant ssh
cd /myresel
python3 manage.py rqworker default &
python3 manage.py runserver 0.0.0.0:8000
````

Sur votre navigateur web rendez-vous sur :
 - `http://10.0.3.94:8000` Pour simuler le VLAN 994 (depuis l'exterieur)
 - `http://10.0.3.95:8000` Pour simuler le VLAN 995 (depuis le réseau d'inscription)
 - `http://10.0.3.99:8000` Pour simuler le VLAN 999 (Depuis une machine inscrite)
 - `http://10.0.3.199:8000` Pour simuler le VLAN 999 (Depuis une machine non inscrite)

Votre adresse MAC sera par défaut : "0a:00:27:00:00:10", Vous pouvez la changer dans le fichier `myresel/settings_local.py`.


### Tests
En plus des tests "manuels", l'application présente des tests automatisés qui permettent de vérifier le bon fonctionnement des parties critiques de l'application. Lorsque vous ajoutez du code, **créez des tests** ! [En plus c'est très simple avec Django...](https://docs.djangoproject.com/en/1.10/topics/testing/)


Pour lancer les tests :
```
python3 manage.py tests
```

**Ne lancez surtout pas les tests sur le ldap de production !** [Pika](mailto:pika@resel.fr) risque d'avoir des surprises.

## Liste des modules

### Modules

 - `myresel/` : contient l'ensemble des fichier de configuration de l'application. Le fichier `settings.py` contient la configuration indépendante de l'installation et le fichier `settings_local.py` contient la configuration qui spécifique de l'installation.
 - `ldapback/` : wrapper vers le backend ldap qui simule les models django. Voir [ldapback/README.md](ldapback/README.md) pour plus d'informations
 - `fonctions/` : des fonctions génériques utiles (en cours de depreciation)
 - `gestion_personnes/` : tout ce qui touche à la gestion des comptes utilisateurs
 - `gestion_machines/` :  tout ce qui touche à la gestion des machines
 - `tresorerie/` : la tréso obvously
 - `clubs/` : Gestion des clubs
 - `whoswho/` : La gestion de l'annuaire
 - `wiki/` :  le wiki destiné aux utilisateurs. Actuellement il est éditable uniquement par les administrateurs
 - `pages/` : les pages statiques et principales
 
### Autres dossiers
 
 - `locale/` : les fichiers de langue
 - `static/` : les fichiers statiques (js, img, css...)
 - `templates/` : les templates généraux à l'application 
 - `vagrant/` : les fichiers de configuration spécifiques à Vagrant
 
 
## Conventions et bonnes pratiques 
 
Ici, on a des nazis du [PEP8](https://www.python.org/dev/peps/pep-0008/), donc respectez le. Si vous ne le connaissez pas et n'aimez pas lire les trucs compliqués [voici un petit résumé](http://sametmax.com/le-pep8-en-resume/).
 
Le nom des entités (modules, fonctions, classes, variables...) doit toujours être en anglais, pour les commentaires et les docstrings on est plus souple et le français est toléré. Vous constaterez que ceci n'est pas toujours respecté, c'est pas une raison pour continuer rajouter du français dans le code !
 
Toutes les fonctions et classes doivent avoir un docstring sauf quand le code est vraiment évident. Aussi, un bon commentaire n'explique ce que fait le code, mais pourquoi ce bout de code existe.

## Inscription

Du fait de l'architecture très spécialisée du ResEl, toute les fonctionnalités touchants à l'inscription et la gestion des machines sont sensibles. En effet, pour détecter la bonne addresse MAC et pour proposer un site différent dépendant de l'origine de l'utilisateur, il est nécéssaire de mettre la machine sur plusieurs réseaux.  

Dépendant du VLAN d'origine, le serveur NGINX taggera les requêtes HTTP différement. Puis, en fonction du tag les middlewares `NetworkConfiguration` et `inscriptionNetworkHandler` ajouterons des métadonnées aux requetes (comme par exemple l'adresse mac de l'utilisateur) puis vont rerouter les requêtes vers les bonnes vues.

Dans l'environnement de développement, comme il est extrêmement compliqué de totalement simuler l'architecture du ResEl, le choix a été fait de créer un nouveau middleware `SimulateProductionNetwork` qui empoisonera les requetes avec de fausses ip.
 
 ---------------------------------------------
 
## Environment de production
 
Actuellement le site est fonctionnel sur les serveurs skynet à Brest et doubidou à Rennes. Voici la démarche d'installation. 
 
### Configuration matérielle

Pour que le site puisse facilement détecter les addresses MAC des machines lors de l'inscription, celui-ci a besoin de plusieurs interfaces réseau :
 - **eth0** : VLAN 997 Administration
 - **eth1** : VLAN 994 Vue publique (également passerelle par défaut)
 - **eth2** : VLAN 999 Vue depuis l'interieur du ResEl machines inscrites (bien choisir l'ip)
 - **eth3** : VLAN 999 Vue depuis les machines non inscrites (bien choisir l'ip)
 - **eth4** : VLAN 995 Vue depuis les machines non inscrites

**Le nom des interfaces est important** pour le lookup dans la table arp, pour le moment ceci n'est pas configurable.

1 à 2 Go de RAM est suffisant dépendant du nombre d'utilisateurs qui s'inscrivent.

10 Go de disque est confortable (même avec latex, oui difficile de me croire !)

### Configuration du DNS et du DHCP
TODO

### Exceptions au Firewall

Pour que le site fonctionne parfaitement il faut que les utilisateurs puissent payer en ligne et puissent se connecter depuis le CAS école. Il faut donc ouvrir les 2 ip dans firewall pour que l'on puisse accéder à ces sites depuis le VLAN d'inscription.

### Installation de base

Installez une machine proprement comme on le fait au ResEl, avec Debian, Munin, Icinga, Backuppc, le proxy http bien configuré. Avec un peu de change vous ferez ça avec Ansible, mais je ne me fais pas trop d'illusions non plus...

Installez les paquets nécéssaires :
```
apt install build-essential python-software-properties python3 python3-dev python3-pip nginx libmysqlclient-dev ldap-utils libldap2-dev libsasl2-dev libssl-dev redis-server libjpeg-dev libssl-dev gettext supervisor
apt install texlive-latex-extra  # Ne pas executer si vous voulez économiser un café
```

### Configuration de nginx
Créez un site resel.fr

Exemple : `/etc/nginx/sites-available/resel.fr` dans le fichier `nginx.conf`  

### Configuration de uwsgi
Todo

### Configuration de Supervisor
Supervisor nous permet de s'assurer que les taches de fond soient bien tout le temps en marche et qu'il ne faille pas les relancer à la main à chaque fois.

Créer le fichier `/etc/supervisor/conf.d/resel.fr.conf` :
TODO: centraliser les logs... 

```
[program:rqworker]
command=/srv/www/resel.fr/env/bin/python manage.py rqworker
directory=/srv/www/resel.fr
user=www-data
```

### Configuration du site
Si il n'existe pas déjà creez un utilisateur `www-data` il sera le owner du programme.
Créez également le dossier `/srv/www/` et déplacez-vous y dedans.

Puis téléchargez le site :
```
git clone https://git.resel.fr/resel/myresel resel.fr
cd resel.fr
```

Créez le fichier `myresel/settings_local.py` et remplissez-le convenablement en vous inspirant du fichier `myresel/settings_local.py.tpl`.

TODO

### Lancement du service

Lancer les services en tache de fond :
```
supervisorctl
start rqworker
```

Démarrez nginx :
```
systemctl start nginx
```

### Monitoring
Configurer icinga et tout...

Supervisor : https://github.com/nationbuilder/supervisord-nagios

TODO: nginx, veronica, mails...

En cas de bug détecté, le site envoie automatiquement un mail à botanik, si vous êtes listmaster vous devriez recevoir ces mails.

### Notes

#### Astuces

##### mettre le site en mode maintenance
Lorsque vous avez de grosses migrations à faire, il est parfois nécéssaire de mettre le site en mode maintenance pour éviter que les utilisateurs ecrivent dans la base de données en même temps que vos migrations. Pour cela il suffit de renommer le fichier `maintenance_off.html` en `maintenance_on.html`. Si la configuration de nginx est correcte, le site devrait retourner une erreur `503` le temps de faire la migration. 

-----------------------

## Crédits
Pour ce magnifique site, on peut remercier : 
 - Théo Jacquin @nimag42 : theo.jacquin@telecom-bretagne.eu
 - Morgan Robin @tharkunn : morgan.robin@telecom-bretagne.eu
 - Loïc Carr @dimtion : loic.carr@telecom-bretagne.eu

Code sous license ne faites pas de bêtises.