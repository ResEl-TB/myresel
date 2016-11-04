#!/usr/bin/env bash

# Set default values if values not sets
if [ -z ${MYSQL_PASSWORD+x} ]; then MYSQL_PASSWORD=blah; fi
if [ -z ${MYSQL_DATABASE+x} ]; then MYSQL_DATABASE=resel; fi
if [ -z ${MYSQL_USER+x} ]; then MYSQL_USER=resel; fi
if [ -z ${ROOTDIR+x} ]; then ROOTDIR=/myresel/; fi


mysql -uroot -p${MYSQL_PASSWORD} -e "DROP DATABASE IF EXISTS ${MYSQL_DATABASE};"
mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE DATABASE ${MYSQL_DATABASE}"
mysql -uroot -p${MYSQL_PASSWORD} -e "GRANT ALL PRIVILEGES ON * . * TO '${MYSQL_USER}'@'localhost';"

source ${ROOTDIR}.install/scripts/populate_db.sh