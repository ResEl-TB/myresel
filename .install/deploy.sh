#!/usr/bin/env bash

cd /srv/www/resel.fr/
git pull
source /srv/www/resel.fr/env/bin/activate
python manage.py collectstatic --noinput