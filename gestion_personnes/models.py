# coding: utf-8
import json
import uuid
from datetime import datetime, timedelta

from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models

import ldapback
from fonctions import generic
from ldapback.models.fields import LdapCharField, LdapPasswordField, LdapNtPasswordField, LdapListField, \
    LdapDatetimeField
from myresel.settings import LDAP_DN_PEOPLE


class LdapUser(ldapback.models.LdapModel):
    """
    The class having all the element for a user
    """
    base_dn = LDAP_DN_PEOPLE
    object_classes = ['genericPerson', 'enstbPerson', 'reselPerson', 'maiselPerson', 'aePerson', 'mailPerson']

    # genericPerson
    uid = LdapCharField(db_column='uid', object_classes=['genericPerson'], pk=True)
    first_name = LdapCharField(db_column='firstname', object_classes=['genericPerson'])
    last_name = LdapCharField(db_column='lastname', object_classes=['genericPerson'])
    user_password = LdapPasswordField(db_column='userpassword', object_classes=['genericPerson'])
    nt_password = LdapNtPasswordField(db_column='ntpassword', object_classes=['genericPerson'])
    display_name = LdapCharField(db_column='displayname', object_classes=['genericPerson'])
    postal_address = LdapCharField(db_column='postaladdress', object_classes=['genericPerson'])

    # reselPerson
    inscr_date = LdapDatetimeField(db_column='dateinscr', object_classes=['reselPerson'])
    cotiz = LdapListField(db_column='cotiz', object_classes=['reselPerson'])
    end_cotiz = LdapDatetimeField(db_column='endinternet', object_classes=['reselPerson'])
    campus = LdapCharField(db_column='campus', object_classes=['reselPerson'])

    # maiselPerson
    building = LdapCharField(db_column='batiment', object_classes=['maiselPerson'])
    room_number = LdapCharField(db_column='roomnumber', object_classes=['reselPerson'])
    # TODO: coupure

    # enstPerson
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
    # TODO : publiable
    # TODO : altmail


    # aePerson
    ae_cotiz = LdapCharField(db_column='aeCotiz', object_classes=['aePerson'])
    ae_nature = LdapCharField(db_column='aeNature', object_classes=['aePerson'])
    n_adherent = LdapCharField(db_column='nAdherent', object_classes=['aePerson'])
    # TODO: other fields


    # mailPerson
    mail_local_address = LdapListField(db_column='mailLocalAddress', object_classes=['mailPerson'])
    mail_dir = LdapCharField(db_column='mailDir', object_classes=['mailPerson'])
    home_directory = LdapCharField(db_column='homeDirectory', object_classes=['mailPerson'])

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @classmethod
    def from_json(cls, json_input):
        obj_dict = json.loads(json_input)
        self = cls()
        for k, v in obj_dict.items():
            self.__dict__[k] = v
        return self

    def need_to_pay(self):
        if not self.end_cotiz:
            return 'danger'
        now = datetime.now()
        if self.end_cotiz < now:
            return 'danger'
        elif self.end_cotiz < (now + timedelta(days=7)):
            return 'warning'
        else:
            return 'success'

    @staticmethod
    def generate_address(campus, building, room):
        if campus.lower() == "brest":
            address = "Bâtiment {} Chambre {} Maisel Télécom Bretagne\n 655 avenue du Technopôle 29280 Plouzané"
        else:
            address = "Bâtiment {} Chambre {} Maisel Télécom Bretagne\n 2, rue de la Châtaigneraie 35576 Cesson Sévigné"
        address = address.format(
            building,
            room,
        )

        return address

    def is_member(self):
        return str(generic.current_year()) in [c.strip() for c in self.cotiz]


class LdapOldUser(LdapUser):
    """
    This model represent an old user that is no longer in the active users
    """
    base_dn = LDAP_DN_PEOPLE = "ou=anciens,dc=maisel,dc=enst-bretagne,dc=fr"


class UserMetaData(models.Model):
    """
    Class to store a bit more information about users which are only important for
    this site, and not all the ResEl
    """
    uid = models.CharField(max_length=64, primary_key=True)
    email_validation_code = models.UUIDField(default=uuid.uuid4)
    email_validated = models.BooleanField(default=False)
    reset_pwd_code = models.UUIDField(default=uuid.uuid4)

    def do_reset_pwd_code(self):
        self.reset_pwd_code = uuid.uuid4()
        self.save()

    def send_email_validation(self, email, link_builder):
        """
        Send a new validation email.
        WARNING: it will assume that the email was never validated!
        :param link_builder: a link builder from a request for example : request.build_absolute_uri()
        :param email: the email of the user
        :return:
        """
        # Generate a new uid
        self.email_validation_code = uuid.uuid4()
        self.email_validated = False
        self.save()

        user_email = EmailMessage(
            subject="Validation addresse e-mail ResEl",
            body=("Bonjour,\n\n" +
                  "Voici le lien de validation de votre addresse e-mail : \n" +
                  "%s\n\n" +
                  "------------------------\n\n" +
                  "Il est important de garder vos informations personnelles à jour.\n\n"
                  "Si vous pensez que vous recevez cet e-mail par erreur, veuillez l'ignorer. Dans tous les cas, n'hésitez pas à nous contacter " +
                  "à support@resel.fr pour toute question.") % (
                     link_builder(reverse('gestion-personnes:check-email',
                                          kwargs={'key': self.email_validation_code}))
            ),
            from_email="secretaire@resel.fr",
            reply_to=["support@resel.fr"],
            to=[email],
        )

        user_email.send()
