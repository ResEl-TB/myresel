#!/usr/bin/env bash

python3 ${ROOTDIR}manage.py makemigrations pages tresorerie wiki
python3 ${ROOTDIR}manage.py migrate
python3 ${ROOTDIR}populate_ldap.py