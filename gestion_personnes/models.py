# coding=utf-8
import json

import ldapback
import ldapdb
from django.db import models

# DO NOT INHERIT MODELS, it won't work on the ldap

# Create your models here.
from ldapback.models.fields import LdapCharField, LdapPasswordField, LdapNtPasswordField, LdapListField
from myresel.settings import LDAP_DN_PEOPLE
from ldapdb.models.fields import CharField, IntegerField, ListField


# TODO: change class name
class LUser(ldapback.models.LdapModel):
    """
    The class having all the element for a user
    """
    base_dn = LDAP_DN_PEOPLE
    object_classes = ['genericPerson', 'enstbPerson', 'reselPerson', 'maiselPerson', 'aePerson']

    # genericPerson
    uid = LdapCharField(db_column='uid', object_classes=['genericPerson'], pk=True)
    first_name = LdapCharField(db_column='firstname', object_classes=['genericPerson'])
    last_name = LdapCharField(db_column='lastname', object_classes=['genericPerson'])
    user_password = LdapPasswordField(db_column='userpassword', object_classes=['genericPerson'])
    nt_password = LdapNtPasswordField(db_column='ntpassword', object_classes=['genericPerson'])
    display_name = LdapCharField(db_column='displayname', object_classes=['genericPerson'])
    postal_address = LdapCharField(db_column='postaladdress', object_classes=['genericPerson'])

    # reselPerson
    inscr_date = LdapCharField(db_column='dateinscr', object_classes=['reselPerson'])
    cotiz = LdapCharField(db_column='cotiz', object_classes=['reselPerson'])
    end_cotiz = LdapCharField(db_column='endinternet', object_classes=['reselPerson'])
    campus = LdapCharField(db_column='campus', object_classes=['reselPerson'])

    # maiselPerson
    building = LdapCharField(db_column='batiment', object_classes=['maiselPerson'])
    room_number = LdapCharField(db_column='roomnumber', object_classes=['reselPerson'])
    # # TODO: coupure
    #
    # # enstPerson
    promo = LdapCharField(db_column='promo', object_classes=['enstbPerson'])
    mail = LdapCharField(db_column='mail', object_classes=['enstbPerson'])
    anneeScolaire = LdapCharField(db_column='anneeScolaire', object_classes=['enstbPerson'])
    mobile = LdapCharField(db_column='telephoneNumber', object_classes=['enstbPerson'])
    option = LdapCharField(db_column='option', object_classes=['enstbPerson'])
    formation = LdapCharField(db_column='formation', object_classes=['enstbPerson'])
    photo_file = LdapCharField(db_column='photoFile', object_classes=['enstbPerson'])
    uid_godchildren = LdapListField(db_column='uidFillot', object_classes=['enstbPerson'])
    uid_godparents = LdapListField(db_column='uidParrain', object_classes=['enstbPerson'])
    origin = LdapCharField(db_column='provenance', object_classes=['enstbPerson'])
    # # TODO : publiable
    # # TODO : altmail
    #
    # # aePerson
    ae_cotiz = LdapCharField(db_column='aeCotiz', object_classes=['aePerson'])
    ae_nature = LdapCharField(db_column='aeNature', object_classes=['aePerson'])
    n_adherent = LdapCharField(db_column='nAdherent', object_classes=['aePerson'])
    # TODO: other fields

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @staticmethod
    def from_json(json_input):
        obj_dict = json.loads(json_input)
        self = LdapUser()
        for k, v in obj_dict.items():
            self.__dict__[k] = v
        return self


class LdapPerson(ldapdb.models.Model):
    """
    Used to search in database if a user exist
    """
    base_dn = LDAP_DN_PEOPLE

    uid = CharField(db_column='uid', max_length=12, primary_key=True)
    firstname = CharField(db_column='firstname', max_length=50)
    lastname = CharField(db_column='lastname', max_length=50)


class LdapUser(ldapdb.models.Model):
    """
    Represent a user in the ldap
    """

    base_dn = LDAP_DN_PEOPLE
    object_classes = ['genericPerson', 'enstbPerson', 'reselPerson', 'maiselPerson']  # TODO: choose wisely

    # genericPerson attributes
    uid = CharField(db_column='uid', max_length=12, primary_key=True)
    firstname = CharField(db_column='firstname', max_length=50)
    lastname = CharField(db_column='lastname', max_length=50)
    displayname = CharField(db_column='displayname', max_length=100)
    userPassword = CharField(db_column='userPassword', max_length=100)
    ntPassword = CharField(db_column='ntPassword', max_length=100)

    # enstPerson attributes
    promo = CharField(db_column='promo', max_length=100)
    mail = CharField(db_column='mail')
    anneeScolaire = CharField(db_column='anneeScolaire')
    mobile = CharField(db_column='telephoneNumber', max_length=32)
    option = CharField(db_column='option')

    # reselPerson attributes
    dateInscr = CharField(db_column='dateInscr')
    cotiz = CharField(db_column='cotiz')
    endCotiz = CharField(db_column='endInternet')
    campus = CharField(db_column='campus')
    batiment = CharField(db_column='batiment')
    roomNumber = CharField(db_column='roomNumber')

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @staticmethod
    def from_JSON(json_input):
        obj_dict = json.loads(json_input)
        self = LdapUser()
        for k, v in obj_dict.items():
            self.__dict__[k] = v
        return self
