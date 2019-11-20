FROM debian:buster
ARG LDAPPASSWD

MAINTAINER nicolas@vuillermet.bzh

RUN apt-get -qq update

RUN apt-get -qq upgrade && apt-get install -qq locales locales-all
ENV LC_ALL fr_FR.UTF-8
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR.UTF-8

# Python
COPY .install/scripts/install_essentials.sh install_essentials.sh
RUN chmod +x install_essentials.sh
RUN ./install_essentials.sh

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN dig files.pythonhosted.org && traceroute files.pythonhosted.org && ping files.pythonhosted.org -c 5
RUN pip3 install --default-timeout=120 -qr requirements.txt

# LDAP
RUN apt-get -qq upgrade && apt-get -qq install expect ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi

COPY .install/scripts/install_slapd.sh install_slapd.sh
RUN chmod +x install_slapd.sh
RUN ./install_slapd.sh $LDAPPASSWD

# Latex
# RUN apt-get -qq upgrade && apt-get -qq install texlive-latex-extra
# RUN apt-get -qq upgrade && apt-get -qq install libjpeg-dev gettext
