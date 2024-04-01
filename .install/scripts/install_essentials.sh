#!/usr/bin/env bash
apt-get -qq update

if [ "$1" = "no-upgrade" ] ; then
    echo "pass upgrade"
else
    apt-get -qq upgrade
fi

apt-get -qq install build-essential python3-software-properties python3 python3-dev python3-pip vim libssl-dev default-libmysqlclient-dev gcc pkg-config
#easy_install3 -U pip  # Solve debian bug
