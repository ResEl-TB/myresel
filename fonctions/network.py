# coding=utf-8
import logging
import os
import re
import subprocess

from fonctions.generic import is_ip_in_subnet
from myresel import settings

logger = logging.getLogger(__name__)

class NetworkError(Exception):
    """
    An exeption which handle network errors
    """
    pass


def get_mac(ip):
    """
    This function retrieve the mac address of a user based on his ip
    Should be called only if the ip is in the same network
    """

    if settings.DEBUG or settings.TESTING:
        return settings.DEBUG_SETTINGS['mac']

    # TODO : move interfaces to configuration file
    if re.match(r'^172\.[22-23]\.22[4-5]', ip):
        eth = 'eth4'
    elif re.match(r'^172\.[22-23]\.22[6-7]', ip):
        eth = 'eth3'
    else:
        eth = 'eth2'

    try:
        subprocess.check_call(
            ['fping', '-t', '100', '-c', '1', '-I', eth, ip],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    except Exception as e:
        e = NetworkError("An error occurred when doing an fping : "
                     "\n %s" % e)
        logger.error(e)
    mac = str(subprocess.Popen(["arp -a | grep {}\) | grep {} | awk '{{print $4}}'".format(ip, eth)],
                               stdout=subprocess.PIPE,
                               shell=True).communicate()[0]).split('\'')[1].split('\\n')[0]

    m = re.match(r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$', mac)
    if not m:
        raise NetworkError("The string %s is not a valid mac address" % mac)
    return mac


def get_campus(ip):
    """ Détermine le campus en fonction de l'ip de l'utilisateur """

    if ip.startswith('172.22.'):
        return 'Brest'
    elif ip.startswith('172.23.'):
        return 'Rennes'
    else:
        raise NetworkError("The ip %s is not on any campus" % ip)


def update_all():
    """ Relance le DNS, le DHCP et le firewall """
    # TODO: do that in background
    os.system('ssh -t reloader@saymyname')
    os.system('ssh -t updatefirewall@zahia -p 2222')


def is_resel_ip(ip):
    """ Check si l'IP est ResEl """
    try:
        get_campus(ip)
        return True
    except NetworkError:
        return False


def get_network_zone(ip):
    """ 
    Renvoit la zone à laquelle correspond l'ip :
    - Brest-user, Brest-inscription-999, Brest-inscription, Rennes-user, Rennes-inscription
    """

    if is_ip_in_subnet(ip, '172.22.224.0', 23):
        return "Brest-inscription"
    elif is_ip_in_subnet(ip, '172.22.226.0', 23):
        return "Brest-inscription-999"
    elif ip.startswith('172.22.') and ip[7:10].isdigit() and 200 <= int(ip[7:10]) <= 223:  # range 172.22.200.1 to 172.22.223.254
        return "Brest-user"
    elif ip.startswith('172.22.'):
        return "Brest-other"
    elif is_ip_in_subnet(ip, '172.23.224.0', 23):
        return "Rennes-inscription"
    elif ip.startswith('172.23'):  # TODO : check the full pattern
        return "Rennes-user"

    return "Internet"
