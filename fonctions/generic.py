# -*- coding: utf-8 -*-

import binascii
import hashlib
import os
from base64 import decodebytes, encodebytes
from datetime import datetime, time, date
from passlib.hash import nthash


def current_year():
    """ Fonction qui calcule l'année scolaire en cours """

    year = datetime.now().year
    month = datetime.now().month

    if month <= 7:
        year -= 1

    return year

def next_august_fifteenth():
    return datetime(current_year() + 1, 8, 15).astimezone()

def today():
    """ Returns the current day's date"""
    return datetime.combine(date.today(), time()).astimezone()

def hash_passwd(password):
    """ Fourni un hash du passwd utilisateur pour le stocker dans le LDAP """

    salt = os.urandom(4)
    h = hashlib.sha1(password.encode('utf-8'))
    h.update(salt)
    return "{SSHA}" + str(encodebytes(h.digest() + salt)).split("'")[1].split('\\')[0]


def compare_passwd(passwd, hsh):
    if isinstance(hsh, str):
        hsh = hsh.encode('utf-8')
    digest_salt = decodebytes(hsh[6:])
    salt = digest_salt[-4:]
    digest = digest_salt[:-4]
    if isinstance(passwd, str):
        passwd = passwd.encode('utf-8')
    h = hashlib.sha1(passwd)
    h.update(salt)
    return h.digest() == digest


def hash_to_ntpass(password):
    """ Fourni un hash du mdp pour correspondre avec le loggin over Wi-Fi """

    return nthash.hash(password).upper()


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
