#!/usr/bin/env bash

# Bootstrap script for resel

# Configuration
ROOTDIR=/myresel/
ETCDIR=vagrant/etc/

# TODO: move that to python config
LDAP_PASSWD=blah
LDAP_DOMAIN="maisel.enst-bretagne.fr"
LDAP_ORGANISATION="ou=people,dc=maisel,dc=enst-bretagne,dc=fr"

SQLHOST=localhost
SQLNAME=resel
SQLUSER=resel
SQLPASSWD=blah

export DEBIAN_FRONTEND=noninteractive

echo 'apt-get update'
apt-get -qq update

echo 'Installing : build-essential python-software-properties python3 python3-dev python3-pip'
apt-get -qq install build-essential python-software-properties python3 python3-dev python3-pip vim

echo "Installing mysql"
echo "mysql-server mysql-server/root_password password $SQLPASSWD" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again password $SQLPASSWD" | debconf-set-selections
apt-get -qq install mysql-server
apt-get -qq install libmysqlclient-dev

echo "configuring slapd for first run"


apt-get -qq install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi

cd $ROOTDIR
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

service slapd stop
service slapd start

#
#echo "Installing other dependecies"
#apt-get -y install libjpeg-dev
##apt-get install libssl-dev
#
#echo "Installing Python requirements"
#pip3 install -r $ROOTDIR/requirements.txt