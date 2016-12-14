FROM docker.resel.fr/debian:v1

MAINTAINER loic.carr@resel.fr

# Python
RUN apt-get -qq install build-essential python-software-properties python3 python3-dev python3-pip vim libssl-dev libmysqlclient-dev
RUN easy_install3 -U pip

# LDAP
RUN apt-get -qq install slapd ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi

# Latex
RUN apt-get -qq install texlive-latex-extra
RUN apt-get -qq install libjpeg-dev gettext