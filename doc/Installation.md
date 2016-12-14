Installation d'un environement de production
============================================

ce guide détaille comment installer un environement de production complet sur
une machine vierge.

Actuellement le site est fonctionnel sur les serveurs skynet à Brest et doubidou à Rennes. Le déploiement sur les machines se fait automatiquement par le biais de la branche `deploy` et des runners Gitlab.


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

Installez les paquets nécessaires :
```
apt install build-essential python-software-properties python3 python3-dev python3-pip nginx libmysqlclient-dev ldap-utils libldap2-dev libsasl2-dev libssl-dev redis-server libjpeg-dev libssl-dev gettext supervisor
apt install texlive-latex-extra  # Ne pas executer si vous voulez économiser un café
```

### Configuration de nginx
Créez un site resel.fr

#### Configuration du site
Exemple de `/etc/nginx/sites-available/resel.fr` dans le fichier `.install/etc/nginx.conf`  


#### Configuration des hooks (optionnel)
Les hooks permettent de mettre automatiquement à jour le code lorsque celui-ci est déployé.

Les hooks utilisent la syntaxe lua pour nginx, pour les faire fonctionner vous devez ajouter le packet :
```
apt install nginx-extras
```

Exemple de hook dans le fichier `.install/etc/nginx-hook.conf` à mettre dans le fichier `/etc/nginx/sites-available/hook`

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

Le monitoring sur l'application est multiple, cela permet d'avoir le plus de métriques possible en fonction des problèmes rencontrés. Ceux-là vont des métriques "normales" du ResEl à d'autres plus poussées

Installez le service sur une machine du ResEl bien configurée avec [Munin](https://munin.resel.fr) et [Icinga](https://icinga.resel.fr).

Il existe un plugin pour icinga de supervisor : 

Supervisor : https://github.com/nationbuilder/supervisord-nagios


TODO: nginx, veronica, mails...

En cas de bug détecté, le site envoie automatiquement un mail à botanik, si vous êtes listmaster vous devriez recevoir ces mails.