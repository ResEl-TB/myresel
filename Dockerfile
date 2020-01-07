FROM debian:stretch
ARG LDAPPASSWD

MAINTAINER nicolas@vuillermet.bzh

ENV LC_ALL fr_FR.UTF-8
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR.UTF-8

RUN apt -qq update; \
    apt install -qq software-properties-common -y; \
    echo /dev/null >> /etc/apt/sources.list; \
    add-apt-repository "deb [arch=amd64] http://deb.debian.org/debian/ stretch main"; \
    add-apt-repository "deb [arch=amd64] http://security.debian.org/ stretch/updates main"; \
    add-apt-repository "deb [arch=amd64] http://deb.debian.org/debian/ stretch-updates main";


RUN apt -qq update && apt -qq upgrade -y && apt install -qq locales locales-all -y

COPY .install/scripts/install_essentials.sh install_essentials.sh
RUN chmod +x install_essentials.sh && ./install_essentials.sh

RUN apt -qq update && apt -qq upgrade -y

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -qr requirements.txt

# LDAP
RUN apt -qq install expect ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi -y

COPY .install/scripts/install_slapd.sh install_slapd.sh
RUN chmod +x install_slapd.sh && ./install_slapd.sh $LDAPPASSWD

# Latex
# RUN apt-get -qq upgrade && apt-get -qq install texlive-latex-extra
# RUN apt-get -qq upgrade && apt-get -qq install libjpeg-dev gettext
