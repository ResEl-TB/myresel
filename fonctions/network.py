# coding=utf-8
import logging
import os
import re
import subprocess
import redis
from ipaddress import ip_address

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

def get_mac(ip):
    """
    This function retrieve the mac address of a user based on his ip
    Should be called only if the ip is in the same network.
    """

    redis_pref = 'mac__'
    # First check if the ip is referenced in the redis server
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB
        )

        mac = r.get('%s%s' % (redis_pref, ip))
        if mac is not None:
            return mac.decode('utf-8')
        else:
            logger.warning(
                'ip address %s not find in redis server, is the network watcher ok?' % ip,
                extra={'ip_address': ip, 'message_code': 'IP_NOT_FIND_REDIS'}
            )
    except redis.exceptions.ConnectionError as e:
        logger.error(
            'Redis Server Unavailable : %s' % str(e),
            extra={'message_code': 'REDIS_CONNECTION_ERROR'},
        )

    # FIXME: I don't know how to test that very well, and indeed during
    # local tests, a fake mac is sent. One day we will have a good enough
    # test suite
    if settings.DEBUG or settings.TESTING:
        return settings.DEBUG_SETTINGS['mac']

    # TODO : move interfaces to configuration file
    if re.match(r'^172\.2[2-3]\.22[4-5]', ip):
        eth = 'eth4'
    elif re.match(r'^172\.2[2-3]\.22[6-7]', ip):
        eth = 'eth3'
    else:
        eth = 'eth2'
    mac = str(subprocess.Popen(["/usr/sbin/arp -an {} | awk ' {{print $4}}'".format(ip)],
                               stdout=subprocess.PIPE,
                               shell=True).communicate()[0]).split('\'')[1].split('\\n')[0]

    if not is_mac(mac):
        raise NetworkError("The string %s is not a valid mac address" % mac)
    return mac


def get_campus(ip_str: str) -> str:
    """ Tells on which campus the user is """

    try:
        ip = ip_address(ip_str)
    except ValueError as e:
        raise NetworkError(str(e))

    if ip in settings.NET_BREST:
        return 'Brest'
    elif ip in settings.NET_RENNES:
        return 'Rennes'
    else:
        raise NetworkError("The ip %s is not on any campus" % ip)


# @job
def update_all():
    """ Relance le DNS, le DHCP et le firewall """
    # TODO: do that in background
    os.system(settings.DNS_DHCP_RELOAD_COMMAND)
    os.system(settings.FIREWALL_RELOAD_COMMAND)


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

    if ip in settings.NET_BREST_INSCR:
        return "Brest-inscription"
    elif ip in settings.NET_BREST_INSCR_999:
        return "Brest-inscription-999"
    elif ip in settings.NET_BREST_USERS:
        return "Brest-user"
    elif ip in settings.NET_BREST:
        return "Brest-other"
    if ip in settings.NET_RENNES_INSCR:
        return "Rennes-inscription"
    elif ip in settings.NET_RENNES_INSCR_999:
        return "Rennes-inscription-999"
    elif ip in settings.NET_RENNES_USERS:
        return "Rennes-user"
    elif ip in settings.NET_RENNES:
        return "Rennes-other"
    return "Internet"

