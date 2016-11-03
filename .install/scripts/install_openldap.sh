#!/usr/bin/env bash

apt-get -qq install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi
service slapd stop

cp -rf "${ETCDIR}ldap/" /etc/

export PASSWD_HASH=$(slappasswd -h {SSHA} -s ${LDAP_PASSWORD})
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