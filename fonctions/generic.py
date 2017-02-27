# -*- coding: utf-8 -*-

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


def sizeof_fmt(num, suffix='o'):
    """
    Human readable file size

    Credit: Sridhar Ratnakumar
    From: https://stackoverflow.com/a/1094933
    :param num:
    :param suffix:
    :return:
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)
