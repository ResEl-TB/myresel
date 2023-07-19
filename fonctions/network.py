# coding=utf-8
import logging
import os
import re

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
