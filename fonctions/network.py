import subprocess

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