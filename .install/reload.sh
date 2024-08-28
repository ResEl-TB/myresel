#!/usr/bin/env bash

set -e

ROOT=/srv/www/resel.fr/
PYTHON=/srv/www/resel.fr/env/bin/python
PIP=/srv/www/resel.fr/env/bin/pip
cd ${ROOT}

echo ''
echo '======================================================================'
echo '> Mise à jour des dépendances python'
${PIP} install -Uqr requirements.txt

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
echo '> Reloading done'