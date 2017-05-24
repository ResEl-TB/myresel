#!/usr/bin/env bash

cp ${ROOTDIR}.install/etc/sources.list /etc/apt/sources.list

apt-get -qq update
apt-get -qq upgrade

apt-get -qq install build-essential python-software-properties python3 python3-dev python3-pip vim libssl-dev libmysqlclient-dev gcc
easy_install3 -U pip  # Solve debian bug
