#!/usr/bin/env bash

ROOT=/srv/www/resel.fr/
PYTHON=/srv/www/resel.fr/env/bin/python
PIP=/srv/www/resel.fr/env/bin/pip

echo '++ script de déployement V2.1\n'

echo '> Téléchargement de la dernière version de myresel'
cd ${ROOT}
git pull

echo '> Mise à jour des dépendances python'
${PIP} install -Uqr requirements.txt

echo '> Mise à jour de la base de données'
echo '>> Désactivé car risqué, faites-le à la main si vous le désirez'
# ${PYTHON} manage.py migrate --noinput

echo '> Collection des fichiers statiques'
${PYTHON} manage.py collectstatic --noinput

echo '> Vérification des droits'
sudo chown www-data:www-data -R ${ROOT}

echo '> Relance du daemon UWSGI'
touch ${ROOT}/uwsgi.ini

echo '> Relance des tâches de fond : rq-scheduler & rq-worker'
sudo systemctl restart rq-scheduler.service
sudo systemctl restart rq-worker.service

