#!/usr/bin/env bash

ROOT=/srv/www/resel.fr/
PYTHON=/srv/www/resel.fr/env/bin/python
PIP=/srv/www/resel.fr/env/bin/pip

cd ${ROOT}
git pull

echo 'Mise à jour des dépendances python'
${PIP} install -ur requirements.txt

echo 'Mise à jour de la base de données'
echo 'Désactivé car risqué'
# ${PYTHON} manage.py migrate --noinput

echo 'Collection des fichiers statiques'
${PYTHON} manage.py collectstatic --noinput

echo 'Relance du daemon UWSGI'
touch ${ROOT}/uwsgi.ini

echo 'Relance de supervisorctl'
sudo supervisorctl reload