#!/usr/bin/env bash

if [ ! -f ${CONFDIR}settings_local.py ]; then
    cp ${CONFDIR}settings_local.py.tpl ${CONFDIR}settings_local.py

    sed -i "/LDAP_PASSWD *=/s/ *=.*/ = \"${LDAP_PASSWORD}\"/" ${CONFDIR}settings_local.py

    sed -i "/DB_NAME *=/s/ *=.*/ = \"${MYSQL_DATABASE}\"/" ${CONFDIR}settings_local.py
    sed -i "/DB_HOST *=/s/ *=.*/ = \"${MYSQL_HOST}\"/" ${CONFDIR}settings_local.py
    sed -i "/DB_USER *=/s/ *=.*/ = \"${MYSQL_USER}\"/" ${CONFDIR}settings_local.py
    sed -i "/DB_PASSWORD *=/s/ *=.*/ = \"${MYSQL_PASSWORD}\"/" ${CONFDIR}settings_local.py

    sed -i "/DB_QOS_NAME *=/s/ *=.*/ = \"${MYSQL_QOS_DATABASE}\"/" ${CONFDIR}settings_local.py
    sed -i "/DB_QOS_HOST *=/s/ *=.*/ = \"${MYSQL_QOS_HOST}\"/" ${CONFDIR}settings_local.py
    sed -i "/DB_QOS_USER *=/s/ *=.*/ = \"${MYSQL_QOS_USER}\"/" ${CONFDIR}settings_local.py
    sed -i "/DB_QOS_PASSWORD *=/s/ *=.*/ = \"${MYSQL_QOS_PASSWORD}\"/" ${CONFDIR}settings_local.py

    sed -i "/REDIS_HOST *=/s/ *=.*/ = \"${REDIS_HOST}\"/" ${CONFDIR}settings_local.py

    sed -i "/LAPUTEX_TOKEN *=/s/ *=.*/ = \"${LAPUEX_PWD}\"/" ${CONFDIR}settings_local.py
fi
