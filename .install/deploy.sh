#!/usr/bin/env bash

ROOT=/srv/www/resel.fr/
PYTHON=/srv/www/resel.fr/env/bin/python

cd ${ROOT}
git pull

echo 'Collection des fichiers statiques'
${PYTHON} manage.py collectstatic --noinput

echo 'Relance du daemon UWSGI'
touch ${ROOT}/uwsgi.ini

echo 'Relance de supervisorctl'
sudo supervisorctl reload