#!/usr/bin/env bash

# Bootstrap script for resel

# Configuration
ROOTDIR=/myresel/
ETCDIR=${ROOTDIR}vagrant/etc/
LIBDIR=${ROOTDIR}vagrant/lib/

# TODO: move that to python config
LDAP_PASSWD=blah
#LDAP_DOMAIN="maisel.enst-bretagne.fr"
#LDAP_ORGANISATION="ou=people,dc=maisel,dc=enst-bretagne,dc=fr"

SQL_HOST=localhost
SQL_DBNAME=resel
SQL_USER=resel
SQL_PASSWD=blah

export DEBIAN_FRONTEND=noninteractive

echo '>>> apt-get update&upgrade'
apt-get -qq update
apt-get -qq upgrade

echo '>>> Installing : build-essential python-software-properties python3 python3-dev python3-pip'
apt-get -qq install build-essential python-software-properties python3 python3-dev python3-pip vim

echo ">>> Installing mysql"
echo "mysql-server mysql-server/root_password password $SQL_PASSWD" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again password $SQL_PASSWD" | debconf-set-selections
apt-get -qq install mysql-server
apt-get -qq install libmysqlclient-dev

echo -e ">>> Setting up MySQL"
mysql -uroot -p${SQL_PASSWD} -e "CREATE DATABASE ${SQL_DBNAME}"
#mysql -uroot -p${SQL_PASSWD} -e "CREATE USER 'root'@'localhost' IDENTIFIED BY '$SQL_PASSWD';"
#mysql -uroot -p${SQL_PASSWD} -e "GRANT ALL PRIVILEGES ON * . * TO 'root'@'localhost';"
mysql -uroot -p${SQL_PASSWD} -e "CREATE USER '$SQL_USER'@'localhost' IDENTIFIED BY '$SQL_PASSWD';"
mysql -uroot -p${SQL_PASSWD} -e "GRANT ALL PRIVILEGES ON * . * TO '$SQL_USER'@'localhost';"

echo ">>> Installing openldap"


apt-get -qq install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi
service slapd stop

cd ${ROOTDIR}
cp -rf "${ETCDIR}ldap/" /etc/

PASSWD_HASH=$(slappasswd -h {SSHA} -s ${LDAP_PASSWD})
echo "rootpw          \"${PASSWD_HASH}\"" >> /etc/ldap/rootdn.ldap

rm -rf /etc/ldap/slapd.d
chmod +r /etc/ldap/slapd.conf
chmod +r /etc/ldap/access.ldap
chmod -R +r /etc/ldap/schema
chmod +r /etc/ldap/rootdn.ldap

mkdir /var/lib/ldap/maisel
mkdir /var/lib/ldap/resel

cp ${LIBDIR}DB_CONFIG_maisel /var/lib/ldap/maisel/DB_CONFIG
cp ${LIBDIR}DB_CONFIG_resel /var/lib/ldap/resel/DB_CONFIG

# TODO: empty (a bit) the database
slapadd -c -l ${LIBDIR}maisel.ldif -b dc=maisel,dc=enst-bretagne,dc=fr
slapadd -c -l ${LIBDIR}resel.ldif -b dc=resel,dc=enst-bretagne,dc=fr

chown -R openldap:openldap /var/lib/ldap/

service slapd start


echo ">>> Installing other dependecies"
apt-get -qq install libjpeg-dev
apt-get -qq install libssl-dev

echo ">>> Installing Python requirements"
pip3 install -r $ROOTDIR/requirements.txt