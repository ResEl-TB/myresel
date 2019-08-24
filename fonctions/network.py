# coding=utf-8
import logging
import os
import re
import subprocess
import redis
from ipaddress import ip_address

from django.core.exceptions import ObjectDoesNotExist
from rq.decorators import job

from myresel import settings

logger = logging.getLogger("default")


class NetworkError(Exception):
    """
    An exeption which handle network errors
    """
    pass

def is_mac(mac):
    """
    :param mac: string to test
    :return:  :bool: True if it is a mac, False otherwise
    """
    return re.match(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$', mac)


def get_campus(ip_str: str) -> str:
    """ Tells on which campus the user is """

    try:
        ip = ip_address(ip_str)
    except ValueError as e:
        raise NetworkError(str(e))

    if ip in settings.NET_BREST or ip in settings.NET_BREST_OLD:
        return 'Brest'
    elif ip in settings.NET_RENNES or ip in settings.NET_RENNES_OLD:
        return 'Rennes'
    else:
        raise NetworkError("The ip %s is not on any campus" % ip)


def update_all():
    """ Reload DNS, DHCP and Firewall configuration """
    # FIXME: do that in background
    # 2018-11-19 dimtion: I would probably not do that in the background.
    # It might be much better to do it with a timeout to avoid waiting
    # for too long. The best would be to make the front-end aware that this
    # action can fail
    try:
        os.system(settings.DNS_DHCP_RELOAD_COMMAND)

        # Disabled firewall reload command as it is automatic:
        # date: 2018-11-19
        # os.system(settings.FIREWALL_RELOAD_COMMAND)

        logger.info(
            "DHCP & DNS reloaded",
                extra={
                    'message_code': 'NETWORK_UPDATE'
                })
    except Exception as e:
        logger.error(
            "Failed to reload DHCP & DNS: %s" % e,
            extra={
                'message_code': 'NETWORK_UPDATE'
            })


def is_resel_ip(ip: str) -> bool:
    """ Check if this is a ResEl IP"""
    try:
        get_campus(ip)
        return True
    except NetworkError:
        return False


def get_network_zone(ip_str: str) -> str:
    """
    Tells in which network is the ip
    :param ip_str: string for the ip (e.g. "172.22.220.224")
    :return: Brest-inscription, Brest-inscription-999, Brest-user, Brest-other,
             Rennes-inscription, Rennes-inscription-999, Rennes-user
             Rennes-other or Internet
    """
    try:
        ip = ip_address(ip_str)
    except ValueError as e:
        raise NetworkError(str(e))

    if ip in settings.NET_BREST or ip in settings.NET_BREST_OLD:
        return "Brest-other"
    elif ip in settings.NET_RENNES or ip in settings.NET_RENNES_OLD:
        return "Rennes-other"
    return "Internet"

