#!/usr/bin/expect
set timeout 2
spawn apt-get -qq install slapd
expect “Mot de passe de l'administrateur :” { send “$1\n” }
interact