#!/usr/bin/env bash

# Configure root password
echo "mysql-community-server mysql-community-server/root-pass password ${MYSQL_PASSWORD}" | debconf-set-selections
echo "mysql-community-server mysql-community-server/re-root-pass password ${MYSQL_PASSWORD}" | debconf-set-selections
apt-get -qq install default-mysql-server || apt-get -qq install mariadb-server || apt-get -qq install mysql-server
systemctl start mariadb 2>/dev/null || systemctl start mysql 2>/dev/null || service mysql start

if mysql -uroot -e "SELECT 1;" >/dev/null 2>&1; then
    MYSQL_ROOT="mysql -uroot"
else
    MYSQL_ROOT="mysql -uroot -p${MYSQL_PASSWORD}"
fi

# Create default database
$MYSQL_ROOT -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};"
$MYSQL_ROOT -e "CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';"
$MYSQL_ROOT -e "GRANT ALL PRIVILEGES ON * . * TO '${MYSQL_USER}'@'localhost';"
$MYSQL_ROOT -e "FLUSH PRIVILEGES;"

# Create QoS database
$MYSQL_ROOT -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_QOS_DATABASE};"
$MYSQL_ROOT -e "CREATE USER IF NOT EXISTS '${MYSQL_QOS_USER}'@'localhost' IDENTIFIED BY '${MYSQL_QOS_PASSWORD}';"
$MYSQL_ROOT -e "GRANT ALL PRIVILEGES ON * . * TO '${MYSQL_QOS_USER}'@'localhost';"
$MYSQL_ROOT -e "FLUSH PRIVILEGES;"
$MYSQL_ROOT ${MYSQL_QOS_DATABASE} < ${LIBDIR}qos_struct.sql
