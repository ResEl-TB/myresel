#!/usr/bin/env bash

python3 ${ROOTDIR}manage.py makemigrations pages tresorerie wiki
python3 ${ROOTDIR}manage.py migrate
python3 ${ROOTDIR}manage.py loaddata ${LIBDIR}/django_dummy_data.json ${LIBDIR}/django_dummy_data_user.json