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

# Redis configuration
export REDIS_HOST=localhost

export DEBIAN_FRONTEND=noninteractive

echo '>>> Updating and installing essentials <<<'
source ${ROOTDIR}.install/scripts/install_essentials.sh

echo ">>> Installing and configuring MySQL <<<"
source ${ROOTDIR}.install/scripts/install_mysql.sh

echo ">>> Installing and configuring OpenLDAP <<<"
source ${ROOTDIR}.install/scripts/install_openldap.sh

echo ">>> Installing redis <<<"
apt-get -qq install redis-server

echo ">>> Installing LateX <<<"
source ${ROOTDIR}.install/scripts/install_latex.sh

echo ">>> Installing Python requirements <<<"
pip3 install -qr ${ROOTDIR}requirements.txt

echo ">>> Initializing repo <<<"
source ${ROOTDIR}.install/scripts/configure.sh

echo ">>> Populating database <<<"
source ${ROOTDIR}.install/scripts/populate_db.sh

echo "================================================"
echo "| My ResEl DEV environment installation done   |"
echo "================================================"
echo "|                                              |"
echo "| Launch the server:                           |"
echo "|  \$ vagrant ssh                              |"
echo "|  \$ cd ${ROOTDIR}                            |"
echo "|  \$ python3 manage.py runserver 0.0.0.0:8000 |"
echo "|                                              |"
echo "| Browse to: https://10.0.3.94:8000/           |"
echo "|                                              |"
echo "================================================"