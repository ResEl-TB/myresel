#!/usr/bin/env bash
apt-get -qq update
apt-get -qq upgrade

apt-get -qq install build-essential python-software-properties python3 python3-dev python3-pip vim libssl-dev libmysqlclient-dev
easy_install3 -U pip  # Solve debian bug