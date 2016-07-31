import subprocess
import os
import re

def get_mac(ip):
    """ Fonction qui récupère l'addresse MAC associée à l'IP de l'utilisateur """

    if re.match(r'172\.22\.22[4-5]', ip):
        eth = 'eth3'
    else:
        eth = 'eth2'
    mac = str(subprocess.Popen(["sudo arping -c 1 -i {} -a {} | awk 'NR == 2 {{print $4}}'".format(eth, ip)], 
                            stdout = subprocess.PIPE, 
                            shell=True).communicate()[0]).split('\'')[1].split('\\n')[0]
    return mac


def get_campus(ip):
    """ Détermine le campus en fonction de l'ip de l'utilisateur """

    if ip.startswith('172.22.'):
        return 'Brest'
    elif ip.startswith('172.23.'):
        return 'Rennes'
    else:
        return False


def update_all():
    """ Relance le DNS, le DHCP et le firewall """
    os.system('ssh -t reloader@saymyname')
    os.system('ssh -t updatefirewall@zahia -p 2222')


def is_resel_ip(ip):
    """ Check si l'IP est ResEl """

    return True if get_campus(ip) else False
