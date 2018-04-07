Contribuer au site ResEl
========================


Pour que le projet ne parte pas en vrille, il est nécessaire de respecter
certaines contraintes de développement. Si ces règles ne sont pas respectées
votre code ne sera pas accepté.

# Avant propos
Avant de vous lancer dans le développement du site il est nécessaire de
maitriser les technologies suivantes :
- [Python 3](https://docs.python.org/3/)
- [Django](https://www.djangoproject.com/)
- [HTML](https://developer.mozilla.org/fr/docs/Web/HTML)
- [CSS](https://developer.mozilla.org/fr/docs/Web/CSS)
- [Git](https://git-scm.com/)

Il est également fortement recommandé de connaitre :
- [Javascript](https://developer.mozilla.org/fr/docs/Web/Javascript)
- [JQuery](https://jquery.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Lightweight Directory Access Protocol (LDAP)](https://fr.wikipedia.org/wiki/Lightweight_Directory_Access_Protocol)

Et si vous matrisez les technos suivantes, vous êtes au top:
- [MySQL](https://www.mysql.fr/)
- [Redis](https://redis.io/), [RQ](http://python-rq.org/) et [Django RQ](https://github.com/ui/django-rq)
- [Latex](https://www.latex-project.org/)
- Des notions de réseau et en particulier les [VLAN](https://en.wikipedia.org/wiki/Virtual_LAN)
- [Vagrant](https://www.vagrantup.com/)

Et si vraiment la nuit vous ne voulez plus dormir :
- [Supervisord](http://supervisord.org/)
- [NGINX](https://www.nginx.com/resources/wiki/)


À noter également qu'une connaissance de l'architecture du ResEl vous est nécessaire.
Vous pouvez trouver toutes les infos sur le [wiki administrateur](https://wiki.resel.fr)


# Tests
En plus des tests "manuels", l'application présente des tests automatisés qui
permettent de vérifier le bon fonctionnement des parties critiques de
l'application. Lorsque vous ajoutez du code, vous **devez** créer des tests
automatisés ! 

Pour lancer les tests existant vous pouvez executer la commande suivante dans
le dossier `/myresel/` :

```
python3 manage.py tests
```

**Ne lancez surtout pas les tests sur le LDAP de production !** [Pika](https://garbage.resel.fr/search/?q=putazizi) risque d'avoir des surprises.


Pour créer de nouveaux tests, n'hésitez pas à [suivre la documentation
Django](https://docs.djangoproject.com/en/1.10/topics/testing/)


# Conventions et bonnes pratiques 
 
Ici, on a des nazis du [PEP8](https://www.python.org/dev/peps/pep-0008/), donc
respectez le. Si vous ne le connaissez pas et n'aimez pas lire les trucs
compliqués [voici un petit résumé](http://sametmax.com/le-pep8-en-resume/).
 
Le nom des entités (modules, fonctions, classes, variables...) doit toujours
être en anglais, pour les commentaires et les
[docstrings](https://www.python.org/dev/peps/pep-0257/) on est plus souple et
le français est toléré. Vous constaterez que ceci n'est pas toujours respecté,
**c'est pas une raison pour continuer rajouter du français dans le code !**
 
Toutes les fonctions et classes doivent avoir un docstring sauf quand le code
est vraiment évident. Aussi, je rappelle qu'un bon commentaire n'explique ce
que fait le code, mais pourquoi ce bout de code existe.


# Déployement

Vous venez de faire une modification du code et vous désirez voir la
modification sur le site ? 

Pour cela il faut que votre code passe les [tests automatisés](https://git.resel.fr/resel/myresel/pipelines). Ensuite [créez une merge request](https://git.resel.fr/resel/myresel/merge_requests/new?merge_request[source_branch]=master&merge_request[source_project_id]=2&merge_request[target_branch]=deploy&merge_request[target_project_id]=2) de la branche [master](https://git.resel.fr/resel/myresel/tree/master) vers la branche [deploy](https://git.resel.fr/resel/myresel/tree/deploy).

Si tous les tests se passent bien, un hook sera executé pour demander aux
serveurs de puller le nouveau code de la branche `deploy`. 

