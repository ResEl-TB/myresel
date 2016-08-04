#!/usr/bin/env bash

# Bootstrap script for myresel

# Configuration
ROOTDIR=/myresel
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
apt-get -y install build-essential python-software-properties python3 python3-dev python3-pip vim

echo "Installing mysql"
echo "mysql-server mysql-server/root_password password $SQLPASSWD" | debconf-set-selections
echo "mysql-server mysql-server/root_password_again password $SQLPASSWD" | debconf-set-selections
apt-get -y install mysql-server > /dev/null 2>&1
apt-get -y install libmysqlclient-dev

echo "configuring slapd for first run"

#echo -e " \
#slapd    slapd/internal/generated_adminpw   password $LDAPPASSWD
#slapd    slapd/password2                    password $LDAPPASSWD
#slapd    slapd/internal/adminpw             password $LDAPPASSWD
#slapd    slapd/password1                    password $LDAPPASSWD
#" | sudo debconf-set-selections

apt-get -y install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi

echo -e " \
slapd slapd/internal/generated_adminpw password ${LDAP_PASSWD}
slapd slapd/internal/adminpw password ${LDAP_PASSWD}
slapd slapd/password2 password ${LDAP_PASSWD}
slapd slapd/password1 password ${LDAP_PASSWD}
slapd slapd/domain string ${LDAP_DOMAIN}
slapd shared/organization string ${LDAP_ORGANISATION}
slapd slapd/backend string HDB
slapd slapd/purge_database boolean true
slapd slapd/move_old_database boolean true
slapd slapd/allow_ldap_v2 boolean false
slapd slapd/no_configuration boolean false
slapd slapd/dump_database select when needed
" | debconf-set-selections

dpkg-reconfigure -f noninteractive slapd

service slapd restart

echo "Installing other dependecies"
apt-get -y install libjpeg-dev
#apt-get install libssl-dev

echo "Installing Python requirements"
pip3 install -r $ROOTDIR/requirements.txt