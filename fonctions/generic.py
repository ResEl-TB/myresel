import binascii, hashlib, os
from base64 import encodestring
from datetime import datetime

def get_year():
    """ Fonction qui calcule l'année scolaire en cours """
    year = datetime.now().year
    month = datetime.now().month

    if month < 6:
        year -= 1

    return year

def get_campus(ip):
    """ Détermine le campus en fonction de l'ip de l'utilisateur """
    if '172.22' in ip:
        return 'Brest'
    else:
        return 'Rennes'

def hash_to_passwd(password):
    """ Fourni un hash du passwd utilisateur pour le stocker dans le LDAP """
    salt = os.urandom(4)
    h = hashlib.sha1(password.encode('utf-8'))
    h.update(salt)
    return "{SSHA}" + str(encodestring(h.digest() + salt)).split("'")[1].split('\\')[0]

def hash_to_ntpass(password):
    """ Fourni un hash du mdp pour correspondre avec le loggin over Wi-Fi """
    return binascii.hexlify(hashlib.new('md4', password.encode('utf-16le')).digest()).upper()