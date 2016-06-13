import subprocess
import os

def get_mac(ip):
    """ Fonction qui récupère l'addresse MAC associée à l'IP de l'utilisateur """

    mac = str(subprocess.Popen(["ip neigh show | grep '{}\\s' | awk '{{print $5}}'".format(ip)], 
                            stdout = subprocess.PIPE, 
                            shell=True).communicate()[0]).split('\'')[1].split('\\n')[0]
    return mac

def get_campus(ip):
    """ Détermine le campus en fonction de l'ip de l'utilisateur """

    if '172.22' in ip:
        return 'Brest'
    elif '172.23' in ip:
        return 'Rennes'
    else:
        return False

def update_all():
    """ Relance le DNS, le DHCP et le firewall """
    os.system('ssh -t reloader@dynasty')
    os.system('ssh -t reloader@saymyname')
    os.system('ssh -t updatefirewall@zahia -p 2222')

def is_resel_ip(ip):
    """ Check si l'IP est ResEl """

    if '172.22' in ip or '172.23' in ip:
        return True

    return False