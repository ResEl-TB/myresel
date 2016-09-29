import binascii
import hashlib
import os
from base64 import encodestring, decodebytes, encodebytes
from datetime import datetime, timedelta


def current_year():
    """ Fonction qui calcule l'année scolaire en cours """

    year = datetime.now().year
    month = datetime.now().month

    if month <= 7:
        year -= 1

    return year


def get_end_date(duree):
    """ Fonction qui renvoie la date actuelle + la durée en jours """

    date = datetime.now() + timedelta(days = duree)
    return date.strftime('%Y%m%d%H%M%S') + 'Z'


def hash_passwd(password):
    """ Fourni un hash du passwd utilisateur pour le stocker dans le LDAP """

    salt = os.urandom(4)
    h = hashlib.sha1(password.encode('utf-8'))
    h.update(salt)
    return "{SSHA}" + str(encodebytes(h.digest() + salt)).split("'")[1].split('\\')[0]


def compare_passwd(passwd, hsh):
    salt = decodebytes(bytes(hsh[6:], 'utf-8'))
    salt = salt[-4:]
    h = hashlib.sha1(passwd.encode('utf-8'))
    h.update(salt)
    return "{SSHA}" + str(encodestring(h.digest() + salt)).split("'")[1].split('\\')[0] == hsh


def hash_to_ntpass(password):
    """ Fourni un hash du mdp pour correspondre avec le loggin over Wi-Fi """

    return str(binascii.hexlify(hashlib.new('md4', password.encode('utf-16le')).digest()).upper()).split('\'')[1]


def ip_to_int(ip):
    """ Convert an IP in int"""
    o = list(map(int, ip.split('.')))
    res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
    return res


def is_ip_in_subnet(ip, ipNetwork, maskLength):
    """ Check if ip is in the subnet ipNetwork/maskLength"""
    ipInt = ip_to_int(ip)
    maskLengthFromRight = 32 - maskLength
    ipNetworkInt = ip_to_int(ipNetwork) #convert the ip network into integer form
    binString = "{0:b}".format(ipNetworkInt) #convert that into into binary (string format)
    chopAmount = 0 #find out how much of that int I need to cut off
    for i in range(maskLengthFromRight):
        if i < len(binString):
            chopAmount += int(binString[len(binString)-1-i]) * 2**i
    minVal = ipNetworkInt-chopAmount
    maxVal = minVal+2**maskLengthFromRight -1
    return minVal <= ipInt and ipInt <= maxVal