Installation d'un environement de production
============================================

Ce guide détaille comment installer un environement de production complet sur
une machine vierge.

Actuellement le site est fonctionnel sur les serveurs `skynet` à Brest et
`doubidou` à Rennes. Le déploiement sur les machines se fait automatiquement
par le biais de la branche `deploy` et des runners Gitlab.


## Configuration matérielle (_**obsolète**_?)

Pour que le site puisse facilement détecter les addresses MAC des machines lors
de l'inscription, celui-ci a besoin de plusieurs interfaces réseau :
 - **eth0** : VLAN 997 Administration
 - **eth1** : VLAN 994 Vue publique (également passerelle par défaut)
 - **eth2** : VLAN 999 Vue depuis l'interieur du ResEl machines inscrites (bien
   choisir l'ip)
 - **eth3** : VLAN 999 Vue depuis les machines non inscrites (bien choisir
   l'ip)
 - **eth4** : VLAN 995 Vue depuis les machines non inscrites

**Le nom des interfaces est important** pour le lookup dans la table arp, pour
le moment ceci n'est pas configurable. Regardez la configuration de `skynet`
pour vous inspirer 1 à 2 Go de RAM est suffisant dépendant du nombre
d'utilisateurs qui s'inscrivent.

* Voir [wiki/Routage](https://wiki.resel.fr/R%C3%A9seau/Routage) pour le bon
  adressage
* Voir [wiki/Installation Serveur](https://wiki.resel.fr/Guides/Installation-serveur)
  pour savoir comment configurer le réseau

5 Go de disque est confortable

## Exceptions au Firewall

Pour que le site fonctionne parfaitement il faut que les utilisateurs puissent
payer en ligne et puissent se connecter depuis le CAS école. Il faut donc
ouvrir les 2 ip dans firewall pour que l'on puisse accéder à ces sites depuis
le VLAN d'inscription.

Pour que les personnes dans la zone d'inscription puissent payer même si elles
n'ont pas internet, il faut rajouter des exeptions au Firewall. Cela est fait
actuellement au moyen d'un script sur `Zahia`. Il est disponible à :
`zahia:/srv/scripts/stripe_ips.py`

## Installation des dépendances

Installez une machine proprement comme on le fait au ResEl, avec Debian, Munin,
Icinga, Backuppc, le proxy http bien configuré. Avec un peu de chance vous
ferez ça avec Ansible, mais je ne me fais pas trop d'illusions non plus...

Installez les paquets nécessaires :
```bash
apt install build-essential nginx pkg-config \
    software-properties-common python3 python3-dev python3-pip \
    python3.11-venv libmariadb-dev-compat libmariadb-dev ldap-utils \
    libldap2-dev libsasl2-dev libssl-dev libjpeg-dev libssl-dev gettext -y
```

### Installation du site

Créez un dossier `/srv/www/resel.fr/`, donnez-le à l'utilisateur `www-data`:
```bash
mkdir -p /srv/www/resel.fr/
chown www-data:www-data /srv/www/resel.fr/
mkdir -p /var/log/nginx/{default,resel.fr,stages.resel.fr}/
touch /var/log/nginx/{default,resel.fr,stages.resel.fr}/{access.log,error.log}
chown www-data:www-data -R /var/log/nginx
```

Téléchargez le site:
```bash
nano /etc/passwd
su -- www-data
cd /srv/www/resel.fr/
git clone https://git.resel.fr/resel/applications-utilisateurs/myresel.git .
git checkout deploy
exit
```

### Configuration de nginx

#### Configuration nginx du site
Vous trouverez dans le fichier  `.install/etc/nginx.conf` un exemple de la
configuration nginx à placer dans : `/etc/nginx/` ainsi que la configuration
uwsgi `.install/etc/resel.fr` à placer dans `/etc/nginx/sites-available`

```bash
cp /srv/www/resel.fr/.install/etc/nginx.conf /etc/nginx/nginx.conf
cp /srv/www/resel.fr/.install/etc/resel.conf /etc/nginx/sites-available/resel.fr
ln -s /etc/nginx/sites-available/resel.fr /etc/nginx/sites-enabled/resel.fr
```
On redémarrera nginx plus tard


#### Configuration des hooks ssh

Les hooks permettent de  mettre à jour automatique l'installation sans avoir
à puller le code à la main.

Créez un utilisateur `deploy` et l'affecter aux bons groupes :
```bash
useradd -m deploy
usermod -aG www-data deploy
```


Afin de pouvoir télécharger les dernières versions sur site ResEl, il faut que
l'utilisateur `deploy` ait les bons droits. Modifier `/etc/passwd` :
```
deploy:x:1004:1005::/home/deploy:/srv/www/resel.fr/.install/deploy.sh
```

Lui créer une clé SSH sans mot de passe:
```bash
ssh-keygen -t ed25519 -f /home/deploy/.ssh/id_rsa
cat /home/deploy/.ssh/id_rsa.pub
exit
```

Ajoutez cette clé aux clés autorisées sur gitlab en l'ajoutant dans l'onglet:
`Settings > Repository > Deploys Keys`

Modifiez `visudo` et ajoutez la ligne suivante : 
```
deploy          ALL=NOPASSWD: /bin/chown, /bin/systemctl, /bin/chmod
```

Enfin on va ajoute sa clé privée au secrets de gitlab:

Copiez la clé : `cat /home/deploy/.ssh/id_rsa`

Dans le repo myresel : `Settings > Pipelines > Secret variables`
Ajoutez une clé par exemple `STAGING_DEPLOY_KEY`


#### Configuration des hooks nginx [obsolète]

:warning: OBSOLÈTE :warning:, veuillez utiliser les hook ssh (décrit par la
suite). Si ceci est laissé c'est parce que ceci est toujours en prod sur 
skynet et doubidou.

Les hooks permettent de mettre automatiquement à jour le code lorsque celui-ci est déployé.

Les hooks utilisent la syntaxe lua pour nginx, pour les faire fonctionner vous devez ajouter le packet :
```
apt install nginx-extras
```

Exemple de hook dans le fichier `.install/etc/nginx-hook.conf` à mettre dans le fichier `/etc/nginx/sites-available/hook`:
```bash
cp /srv/www/resel.fr/.install/etc/nginx-hook.conf /etc/nginx/sites-available/hook
vim /etc/nginx/sites-available/hook
ln -s /etc/nginx/sites-available/hook /etc/nginx/sites-enabled/hook
```


### Configuration de uwsgi
Installer uwsgi:
```bash
pip3 install uwsgi
```

Configurer le service
```bash
cp /srv/www/resel.fr/.install/etc/uwsgi.service /etc/systemd/system/uwsgi.service
chmod +r /etc/systemd/system/uwsgi.service
mkdir touch /var/log/uwsgi/
touch /var/log/uwsgi/emperor.log
chown -R www-data:www-data /var/log/uwsgi
```

Le configurer en copiant les fichiers proposés:
```bash
mkdir -p /etc/uwsgi/vassals
cp /srv/www/resel.fr/.install/etc/uwsgi-emperor.ini /etc/uwsgi/emperor.ini
cp /srv/www/resel.fr/.install/etc/uwsgi-vassal.ini /srv/www/resel.fr/uwsgi.ini
ln -s /srv/www/resel.fr/uwsgi.ini /etc/uwsgi/vassals/resel.fr.ini
```

Configurer nginx pour utiliser uwsgi:
```bash
cp /srv/www/resel.fr/.install/etc/nginx-uwsgi.conf /etc/nginx/conf.d/uwsgi_params.conf
```

### Ajout des cron jobs nécessaires et des services

Nous avons actuellement un job qui tourne régulièrement pour repopuler la base
de donnée REDIS pour choisir une adresse ip.

Il suffit de simplement copier le fichier de cron :
```bash
cp /srv/www/resel.fr/.install/etc/cronfile /etc/cron.d/myresel
```

Pour les services de tâche de fond, comme la création de factures, créez les
services systemd en copiant les fichiers suivants :
```bash
cp /srv/www/resel.fr/.install/etc/rq-worker.service /etc/systemd/system/rq-worker.service
cp /srv/www/resel.fr/.install/etc/rq-scheduler.service /etc/systemd/system/rq-scheduler.service
```


### Configuration du site

Créez le fichier `myresel/settings_local.py` et remplissez-le convenablement en vous inspirant du fichier `myresel/settings_local.py.tpl`.
```bash
cp /srv/www/resel.fr/myresel/settings_local.py.tpl /srv/www/resel.fr/myresel/settings_local.py
vim /srv/www/resel.fr/myresel/settings_local.py
chmod -R www-data .
```

Ne pas oublier en créant la configuration :
* De changer la clé secrête
* De passer `DEBUG` à False
* De bien choisir le campus sur lequel est le site `Brest` ou `Rennes` ou `Nantes`
* D'ajouter les commandes de rechargement du firewall et du DNS
* De configurer les bases de données (ldap, MySQL, QOS, REDIS)
* D'ajouter les clés Stripe (de prod pour la prod)
* De configurer LaPuTeX

### Création du virtual env python

```bash
cd /srv/www/resel.fr/
su -- www-data
python3 -m venv env/
source env/bin/activate
pip3 install -Ur requirements.txt
```

### Ajout des certificats SSL

TODO

- /var/lib/resel/certs/
- /etc/nginx/ssl/2017/resel-fr.conf

### Lancement du service

_**[obsolète]**_ Lancer les services en tache de fond :
```
supervisorctl
start rqworker
systemctl restart cron
```

Lancer les services en tâche de fond :
```
systemctl start rq-worker.service
systemctl start rq-scheduler.service
```

Démarrez nginx et uwsgi:
```
systemctl start uwsgi
systemctl start nginx
```

### Monitoring

Le monitoring sur l'application est multiple, cela permet d'avoir le plus de métriques possible en fonction des problèmes rencontrés. Ceux-là vont des métriques "normales" du ResEl à d'autres plus poussées

Installez le service sur une machine du ResEl bien configurée avec [Munin](https://munin.resel.fr) et [Icinga](https://icinga.resel.fr).

TODO: nginx, veronica, mails...

En cas de bug détecté, le site envoie automatiquement un mail à botanik, si vous êtes listmaster vous devriez recevoir ces mails.


-------

Spécificités d'un environement de staging
=========================================

Au ResEl pour tester le code dans un environement proche de la prod (mais pas
non plus totalement sans limite, nous avons mis en place un environment de
staging. Celui-ci est disponible sur la machine `flea`. Il possède une base de
données séparée pour éviter les conflits avec la principale.

Configuration de mysql

## Installation de MySQL

Inspiré par le fichier `.install/script/install_mysql.sh`

```
apt install mysql-server
mysql -uroot -p
> CREATE DATABASE myresel;
> CREATE USER 'myresel'@'localhost' IDENTIFIED BY 'MOT DE PASSE mysql';
> GRANT ALL PRIVILEGES ON * . * TO 'myresel'@'localhost';

> CREATE DATABASE qos;
> CREATE USER 'qos'@'localhost' IDENTIFIED BY 'MOT DE PASSE qos';
> GRANT ALL PRIVILEGES ON * . * TO 'qos'@'localhost';
> exit

# Populate qos structure:
mysql -uroot qos -p < /srv/www/resel.fr/.install/lib/qos_struct.sql
```

## Installation de OpenLDAP

Inspiré par le fichier `.install/script/install_openldap.sh`

```bash
apt install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi
service slapd stop
cp -rf "/srv/www/resel.fr/.install/etc/ldap/" /etc/
export PASSWD_HASH=$(slappasswd -h {SSHA} -s /MOT DE PASSE/)
echo "rootpw          \"${PASSWD_HASH}\"" >> /etc/ldap/rootdn.ldap

rm -rf /etc/ldap/slapd.d

chmod +r /etc/ldap/slapd.conf
chmod +r /etc/ldap/access.ldap
chmod -R +r /etc/ldap/schema
chmod +r /etc/ldap/rootdn.ldap
mkdir /var/lib/ldap/maisel
mkdir /var/lib/ldap/resel

cp /srv/www/resel.fr/.install/lib/DB_CONFIG_maisel /var/lib/ldap/maisel/DB_CONFIG
cp /srv/www/resel.fr/.install/lib/DB_CONFIG_resel /var/lib/ldap/resel/DB_CONFIG

# Ajout de dumps de la bdd je les ais pris de la bdd de prod:
slapadd -c -l ${LIBDIR}maisel.ldif -b dc=maisel,dc=enst-bretagne,dc=fr
slapadd -c -l ${LIBDIR}resel.ldif -b dc=resel,dc=enst-bretagne,dc=fr

chown -R openldap:openldap /var/lib/ldap/
service slapd start
```

## Install redis server

```bash
apt install redis-server
```


## Configuration du site
```bash
cd /srv/www/resel.fr/
source env/bin/activate
python manage.py collectstatic
python manage.py migrate
touch uwsgi.ini
```
