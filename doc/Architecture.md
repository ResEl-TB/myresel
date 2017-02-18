Architecture du code
====================

Comme tout bon projet Django, le code est découpé en plusieurs modules pour
chacune des fonctionnalités du site. 


## Modules
 - `myresel/` : contient l'ensemble des fichier de configuration de 
 l'application. Le fichier `settings.py` contient la configuration indépendante
  de l'installation et le fichier `settings_local.py` contient la configuration
   qui spécifique de l'installation.
 - `ldapback/` : wrapper vers le backend ldap qui simule les models django. 
 Voir [ldapback/README.md](ldapback/README.md) pour plus d'informations
 - `fonctions/` : des fonctions génériques utiles (en cours de depreciation)
 - `gestion_personnes/` : tout ce qui touche à la gestion des comptes 
 utilisateurs
 - `devices/` :  tout ce qui touche à la gestion des machines
 - `tresorerie/` : la tréso obvously
 - `clubs/` : Gestion des clubs
 - `whoswho/` : La gestion de l'annuaire
 - `wiki/` :  le wiki destiné aux utilisateurs. Actuellement il est éditable 
 uniquement par les administrateurs
 - `pages/` : les pages statiques et principales
 
## Autres dossiers
 - `doc/` : la documentation du site
 - `locale/` : les fichiers de langue
 - `static/` : les fichiers statiques (js, img, css...)
 - `templates/` : les templates généraux à l'application 
 - `.install/` : les fichiers de configuration à l'installation et le 
 déployement de l'application sur les différents environements (Vagrant, 
 gitlab-ci..)

## Les middleware

Pour que le site fonctionne correctement nous avons mis en place plusieurs 
middleware. Tous ces middleware sont décrit dans le fichier `myresel/middleware.py`
et ils sont activés dans le fichier `myresel/settings.py`.

### `IWantToKnowBeforeTheRequestIfThisUserDeserveToBeAdminBecauseItIsAResElAdminSoCheckTheLdapBeforeMiddleware`

Ce middleware permet en fonction des droits admins Ldap de donner les droits
admin à un utilisateur Django. Ce middleware va vérifier qu'une fiche LDAP
admin existe pour l'utilisateur connecté et lui donner les super droits Django
le cas échéant.

### `NetworkConfiguration`

Ce middleware permet de convertir les métadonnées transmises par Nginx au 
serveur afin de les avoir dans n'importe quelle vue Django. Il va mettre
dans le dictionnaire `request.network_data` les informations suivantes :

- `ip` : l'adresse ip de l'utilisateur
- `vlan` : le vlan dans lequel est l'utilisateur (994 si il est à l'extérieur)
- `host` : L'hote HTTP contacté (généralement beta.resel.fr)
- `zone` : La zone dans laquelle est la machine distante (Inscription-Brest,
 Inscription-Rennes, Users...)
- `mac` : Addresse mac de la machine distante (si disponible)
- `is_registered` : la machine est elle enregistré dans le LDAP
- `is_logged_in` : l'utilisateur est-il connecté
- `is_resel` : la machine distantes est-elle dans le ResEl ?
- `device` : si la machine est enregistrée, l'objet LdapDevice associée

### `inscriptionNetworkHandler`

Ce middleware permet de router l'utilisateur vers les vues autorisées lorsqu'il
se trouve dans le VLAN d'inscription.

Ces urls sont définies dans le fichier `myresel/settings.py` :

- `INSCRIPTION_ZONE_ALLOWED_URLNAME` : les URL qui que les utilisateurs ont le
 droit d'accéder depuis le VLAN d'inscription
- `INSCRIPTION_ZONE_ALLOWED_URLNAMESPACE` : Les namespaces d'url qui sont
 autorisés. Cela permet de laisser le droit d'accéder à des modules entier.
- `INSCRIPTION_ZONE_FALLBACK_URLNAME` : L'ip de fallback si un utilisateur 
 demande une page interdite
 
### `SimulateProductionNetwork`

Ce middleware est utile que pendant les tests. Il permet de simuler sans
monter plusieurs machines un environement de test avec plusieurs VLAN.
Cela permet de créer des machines à la volé et sans risque de casser le LDAP.

Ce middleware est désactivé lorsque le site est en production.