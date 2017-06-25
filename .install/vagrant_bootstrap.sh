#!/usr/bin/env bash

# Bootstrap script for resel

# General configuration
export ROOTDIR=/myresel/
export CONFDIR=${ROOTDIR}myresel/
export ETCDIR=${ROOTDIR}.install/etc/
export LIBDIR=${ROOTDIR}.install/lib/

# TODO: move that to python config

# LDAP configuration
export LDAP_PASSWORD=blah

# SQL configuration
export MYSQL_HOST=localhost
export MYSQL_DATABASE=resel
export MYSQL_USER=resel
export MYSQL_PASSWORD=blah

# SQL QoS configuration
export MYSQL_QOS_HOST=localhost
export MYSQL_QOS_DATABASE=qos
export MYSQL_QOS_USER=resel
export MYSQL_QOS_PASSWORD=blah

# Redis configuration
export REDIS_HOST=localhost

# Laputex configuration
export LAPUTEX_HOST='http:\/\/10.0.3.253:8000\/'
export LAPUTEX_PWD='lololol' 

export DEBIAN_FRONTEND=noninteractive

echo '>>> Updating and installing essentials <<<'
source ${ROOTDIR}.install/scripts/install_essentials.sh

echo ">>> Installing and configuring MySQL <<<"
source ${ROOTDIR}.install/scripts/install_mysql.sh

echo ">>> Installing and configuring OpenLDAP <<<"
source ${ROOTDIR}.install/scripts/install_openldap.sh

echo ">>> Installing redis <<<"
apt-get -qq install redis-server

echo ">>> Installing Python requirements <<<"
pip3 install -qUr ${ROOTDIR}requirements.txt

echo ">>> Initializing repo <<<"
source ${ROOTDIR}.install/scripts/configure.sh

echo ">>> Populating database <<<"
source ${ROOTDIR}.install/scripts/populate_db.sh
python3 ${ROOTDIR}manage.py populate_redis

echo "================================================"
echo "| My ResEl DEV environment installation done   |"
echo "================================================"
echo "|                                              |"
echo "| Launch the server:                           |"
echo "|  \$ vagrant ssh                              |"
echo "|  \$ cd ${ROOTDIR}                            |"
echo "|  \$ python3 manage.py rqscheduler &          |"
echo "|  \$ python3 manage.py rqworker &             |"
echo "|  \$ python3 manage.py runserver 0.0.0.0:8000 |"
echo "|                                              |"
echo "| Browse to: https://10.0.3.94:8000/           |"
echo "|                                              |"
echo "================================================"
