#!/usr/bin/env bash

# Bootstrap script for myresel

# Settings :
ROOTDIR=/myresel
LDAPPASSWD=blah

export DEBIAN_FRONTEND=noninteractive

echo 'apt-get update'
apt-get -qq update

echo 'Installing : build-essential python-software-properties python3 python3-dev python3-pip'
apt-get -y install build-essential python-software-properties python3 python3-dev python3-pip


echo -e " \
slapd    slapd/internal/generated_adminpw   password $LDAPPASSWD
slapd    slapd/password2                    password $LDAPPASSWD
slapd    slapd/internal/adminpw             password $LDAPPASSWD
slapd    slapd/password1                    password $LDAPPASSWD
" | sudo debconf-set-selections
apt-get install slapd ldap-utils

pip3 install -r $ROOTDIR/requirements.txt