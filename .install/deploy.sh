#!/usr/bin/env bash

ROOT=/srv/www/resel.fr/
PYTHON=/srv/www/resel.fr/env/bin/python
PIP=/srv/www/resel.fr/env/bin/pip

echo ''
echo '======================================================================'
echo '               script de déployement v2.3                             '
echo '======================================================================'
echo ''

echo ''
echo '======================================================================'
echo '> Téléchargement de la dernière version de myresel'
cd ${ROOT}
git pull

echo ''
echo '======================================================================'
echo '> Mise à jour des dépendances python'
${PIP} install -Uqr requirements.txt

echo ''
echo '======================================================================'
echo '> Mise à jour de la base de données'
echo '>> Désactivé car risqué, faites-le à la main si vous le désirez'
echo '>> Par exemple faites sur skynet:'
echo '>> `\$ python manage.py migrate`'
# ${PYTHON} manage.py migrate --noinput

echo ''
echo '======================================================================'
echo '> Collection des fichiers statiques'
${PYTHON} manage.py collectstatic --noinput

echo ''
echo '======================================================================'
echo '> Compilation des fichiers de langue'
${PYTHON} manage.py compilemessages

echo ''
echo '======================================================================'
echo '> Vérification des droits'
sudo chown www-data:www-data -R ${ROOT}
sudo chmod -R g+rw .

echo ''
echo '======================================================================'
echo '> Relance du daemon UWSGI'
touch ${ROOT}/uwsgi.ini

echo ''
echo '======================================================================'
echo '> Relance des tâches de fond : rq-scheduler & rq-worker'
sudo systemctl restart rq-scheduler.service
sudo systemctl restart rq-worker.service

echo ''
echo '> Déployement done'
