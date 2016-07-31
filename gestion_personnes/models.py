import ldapdb
from django.db import models

# Create your models here.
from myresel.credentials import LDAP_DN_PEOPLE
from ldapdb.models.fields import CharField, IntegerField, ListField


class LdapUser(ldapdb.models.Model):
    """
    Represent a user in the ldap
    """

    base_dn = LDAP_DN_PEOPLE
    object_classes = ['genericPerson', 'enstbPerson', 'reselPerson', 'maiselPerson']

    # genericPerson attributes
    uid = CharField(db_column='uid', max_length=12, primary_key=True)
    firstname = CharField(db_column='firstname', max_lenght=50)
    lastname = CharField(db_column='lastname', max_lenght=50)
    displayname = CharField(db_column='displayname', max_lenght=100)
    userPassword = CharField(db_column='userPassword', max_lenght=100)
    ntPassword = CharField(db_column='ntPassword', max_lenght=100)

    # enstPerson attributes
    promo = CharField(db_column='promo', max_lenght=100)
    mail = CharField(db_column='mail')
    anneeScolaire = CharField(db_column='anneeScolaire')
    mobile = CharField(db_column='phone')
    option = CharField(db_column='option')

    # reselPerson attributes
    dateInscr = CharField(db_column='dateInscr')
    cotiz = CharField(db_column='cotiz')
    endCotiz = CharField(db_column='endCotiz')
    campus = CharField(db_column='campus')
    batiment = CharField(db_column='batiment')
    roomNumber = CharField(db_column='roomNumber')