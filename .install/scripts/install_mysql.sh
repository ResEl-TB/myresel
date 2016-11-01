#!/usr/bin/env bash

echo "mysql-server mysql-server/root_password password ${MYSQL_PASSWORD}" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again password ${MYSQL_PASSWORD}" | debconf-set-selections
apt-get -qq install mysql-server

service mysql start

mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE DATABASE ${MYSQL_DATABASE}"
mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE USER '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';"
mysql -uroot -p${MYSQL_PASSWORD} -e "GRANT ALL PRIVILEGES ON * . * TO '${MYSQL_USER}'@'localhost';"
