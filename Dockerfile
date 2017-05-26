FROM docker.resel.fr/debian:v1

MAINTAINER loic.carr@resel.fr

RUN apt-get -qq update

RUN apt-get -qq upgrade && apt-get install -qq locales locales-all
ENV LC_ALL fr_FR.UTF-8
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR.UTF-8

# Python
RUN apt-get -qq upgrade && apt-get -qq install build-essential python-software-properties python3 python3-dev python3-pip vim libssl-dev libmysqlclient-dev gcc mysql-client
RUN easy_install3 -U pip

COPY requirements.txt requirements.txt
RUN pip3 install -qUr requirements.txt

# LDAP
RUN apt-get -qq upgrade && apt-get -qq install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi

# Latex
RUN apt-get -qq upgrade && apt-get -qq install texlive-latex-extra
RUN apt-get -qq upgrade && apt-get -qq install libjpeg-dev gettext
