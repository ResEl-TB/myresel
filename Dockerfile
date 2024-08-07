FROM debian:12
ARG LDAPPASSWD

ARG DEBIAN_FRONTEND=noninteractive

ENV LC_ALL fr_FR.UTF-8
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR.UTF-8

RUN apt -qq update && apt -qq upgrade -y && apt install -qq locales locales-all software-properties-common -y

COPY .install/scripts/install_essentials.sh install_essentials.sh
RUN chmod +x install_essentials.sh && ./install_essentials.sh

RUN apt -qq update && apt -qq upgrade -y

COPY requirements.txt requirements.txt
RUN pip3 install --break-system-packages -qr requirements.txt

# LDAP
RUN apt -qq install expect ldap-utils libldap2-dev libsasl2-dev libssl-dev ldapvi -y

COPY .install/scripts/install_slapd.sh install_slapd.sh
RUN chmod +x install_slapd.sh && ./install_slapd.sh $LDAPPASSWD


# Latex
# RUN apt-get -qq upgrade && apt-get -qq install texlive-latex-extra
# RUN apt-get -qq upgrade && apt-get -qq install libjpeg-dev gettext
