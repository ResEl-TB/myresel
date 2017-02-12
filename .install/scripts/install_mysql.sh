#!/usr/bin/env bash

# Configure root password
echo "mysql-server mysql-server/root_password password ${MYSQL_PASSWORD}" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again password ${MYSQL_PASSWORD}" | debconf-set-selections
apt-get -qq install mysql-server
service mysql start

# Create default database
mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE DATABASE ${MYSQL_DATABASE}"
mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE USER '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';"
mysql -uroot -p${MYSQL_PASSWORD} -e "GRANT ALL PRIVILEGES ON * . * TO '${MYSQL_USER}'@'localhost';"

# Create QoS database
mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE DATABASE ${MYSQL_QOS_DATABASE}"
mysql -uroot -p${MYSQL_PASSWORD} -e "CREATE USER '${MYSQL_QOS_USER}'@'localhost' IDENTIFIED BY '${MYSQL_QOS_PASSWORD}';"
mysql -uroot -p${MYSQL_PASSWORD} -e "GRANT ALL PRIVILEGES ON * . * TO '${MYSQL_QOS_USER}'@'localhost';"
mysql -uroot -p${MYSQL_PASSWORD} ${MYSQL_QOS_DATABASE} < ${LIBDIR}qos_struct.sql
