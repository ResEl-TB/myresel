FROM debian:jessie

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
RUN pip3 install -qr requirements.txt

# LDAP
RUN apt-get -qq upgrade && apt-get -qq install expect ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi

RUN #!/usr/bin/expect
RUN set timeout 2
RUN spawn apt-get -qq install slapd
RUN expect “Mot de passe de l'administrateur :” { send “$LDAPPASSWD\n” }
RUN interact

# Latex
# RUN apt-get -qq upgrade && apt-get -qq install texlive-latex-extra
# RUN apt-get -qq upgrade && apt-get -qq install libjpeg-dev gettext
