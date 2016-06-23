import binascii, hashlib, os
from base64 import encodestring
from datetime import datetime, timedelta

def get_year():
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
    return "{SSHA}" + str(encodestring(h.digest() + salt)).split("'")[1].split('\\')[0]

def hash_to_ntpass(password):
    """ Fourni un hash du mdp pour correspondre avec le loggin over Wi-Fi """

    return str(binascii.hexlify(hashlib.new('md4', password.encode('utf-16le')).digest()).upper()).split('\'')[1]