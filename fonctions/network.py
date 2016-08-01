import subprocess
import os
import re

from fonction.generic import is_ip_in_subnet

def get_mac(ip):
    """ Fonction qui récupère l'addresse MAC associée à l'IP de l'utilisateur """

    if re.match(r'^172\.22\.22[4-5]', ip):
        eth = 'eth3'
    else:
        eth = 'eth2'
   
    subprocess.check_call(['ping', '-c', '1', '-I', eth, ip], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) 
    mac = str(subprocess.Popen(["arp -a | grep {} | awk '{{print $4}}'".format(ip)], 
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

def get_network_zone(ip):
    """ 
    Renvoit la zone à laquelle correspond l'ip :
    - Brest-user, Brest-inscription-999, Brest-inscription, Rennes-user, Rennes-inscription
    """

    if is_ip_in_subnet(ip, '172.22.224.0', 23):
        return "Brest-inscription"
    else if is_ip_in_subnet(ip, '172.22.226.0', 23):
        return "Brest-inscription-999"
    else if ip.startswith(172.22.) and ip[7:10].isdigit() and 200 <= int(ip[7:10]) <= 223: # range 172.22.200.1 to 172.22.223.254 
        return "Brest-user"
    else if ip.startswith('172.22.'):
        return "Brest-other"
    else if is_ip_in_subnet(ip, '172.23.224.0', 23):
        return "Rennes-inscription"
    else if ip.startswith('172.23'): # TODO : check the full pattern
        return "Rennes-user"

    return "Internet"