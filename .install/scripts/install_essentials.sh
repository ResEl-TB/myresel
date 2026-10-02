#!/usr/bin/env bash
apt-get -qq update

if [ "$1" = "no-upgrade" ] ; then
    echo "pass upgrade"
else
    apt-get -qq upgrade
fi

apt-get -qq install build-essential python3 python3-dev python3-pip python3-venv vim libssl-dev default-libmysqlclient-dev libmariadb-dev libmariadb-dev-compat gcc pkgconf pkg-config
#easy_install3 -U pip  # Solve debian bug
