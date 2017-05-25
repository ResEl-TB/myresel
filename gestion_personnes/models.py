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
    LdapDatetimeField, LdapBooleanField
from myresel.settings import LDAP_DN_PEOPLE
from myresel.settings_local import LDAP_DN_GROUPS


class LdapUser(ldapback.models.LdapModel):
    """
    The class having all the element for a user
    """
    base_dn = LDAP_DN_PEOPLE
    #object_classes = ['genericPerson', 'enstbPerson', 'reselPerson', 'maiselPerson', 'aePerson', 'mailPerson']
    object_classes = LdapListField(db_column='objectClass')

    # genericPerson
    uid = LdapCharField(db_column='uid', object_classes=['genericPerson'], pk=True)
    first_name = LdapCharField(db_column='firstname', object_classes=['genericPerson'])
    last_name = LdapCharField(db_column='lastname', object_classes=['genericPerson'])
    user_password = LdapPasswordField(db_column='userpassword', object_classes=['genericPerson'])
    nt_password = LdapNtPasswordField(db_column='ntpassword', object_classes=['genericPerson'])
    display_name = LdapCharField(db_column='displayname', object_classes=['genericPerson'])
    postal_address = LdapCharField(db_column='postaladdress', object_classes=['genericPerson'])

    # Ldap Groups
    groups = LdapListField(db_column='memberOf')

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
    is_public = LdapBooleanField(db_column='publiable', object_classes=['enstbPerson'])
    birth_date = LdapDatetimeField(db_column='birthDate', object_classes=['enstbPerson'])
    # TODO : altmail


    # aePerson
    ae_cotiz = LdapCharField(db_column='aeCotiz', object_classes=['aePerson'])
    ae_nature = LdapCharField(db_column='aeNature', object_classes=['aePerson'])
    n_adherent = LdapCharField(db_column='nAdherent', object_classes=['aePerson'])
    dates_membre = LdapListField(db_column='datesMembre', object_classes=['aePerson'])
    # TODO: other fields

    # mailPerson
    mail_local_address = LdapListField(db_column='mailLocalAddress', object_classes=['mailPerson'])
    mail_dir = LdapCharField(db_column='mailDir', object_classes=['mailPerson'])
    home_directory = LdapCharField(db_column='homeDirectory', object_classes=['mailPerson'])
    mail_routing_address = LdapCharField(db_column='mailRoutingAddress', object_classes=['mailPerson'])
    mail_del_date = LdapDatetimeField(db_column='mailDelDate', object_classes=['mailPerson'])

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
            address = "Bâtiment {} Chambre {} Maisel Télécom Bretagne\n 655, avenue du Technopôle 29280 Plouzané"
        else:
            address = "Bâtiment {} Chambre {} Maisel Télécom Bretagne\n 2, rue de la Châtaigneraie 35576 Cesson Sévigné"
        address = address.format(
            building,
            room,
        )

        return address

    def is_member(self):
        if isinstance(self.cotiz, list):
            # Pylint disabled because it wrongly guess that self.cotiz is always a LdapListField
            # pylint: disable=not-an-iterable
            return str(generic.current_year()) in [c.strip() for c in self.cotiz]
        return False

    def has_resel_email(self):
        """
        Tells if according to the Ldap the user has a @resel.fr address
        :return: bool
        """
        if isinstance(self.mail_local_address, list):
            # Pylint disabled because it wrongly guess that self.mail_local_address is a LdapListField
            # pylint: disable=unsupported-membership-test
            return 'mailPerson' in self.object_classes and " " not in self.mail_local_address
        else:
            return False

    def is_campus_moderator(self):
        """
        Tels whether the user is allowed to moderate campus emails
        :return: bool
        """
        return LdapGroup.get(pk='campusmodo').is_member(self.uid)


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


class LdapGroup(ldapback.models.LdapModel):
    """
    The class managing the groups in the LDAP
    """

    base_dn = LDAP_DN_GROUPS
    object_classes = ['groupOfNames']

    cn = LdapCharField(db_column='cn', object_classes=['groupOfNames'], pk=True)
    members = LdapListField(db_column='member', object_classes=['groupOfNames'])

    def is_member(self, uid):
        if isinstance(self.members, list):
            # Pylint disabled because it wrongly guess that self.members is a LdapListField
            # pylint: disable=not-an-iterable
            return uid in [member.split(',')[0].split('uid=')[1] for member in self.members]
        return False

    def add_member(self, pk):
        if pk not in self.members:
            # pylint: disable=unsupported-membership-test,no-member
            self.members.append(pk)
            self.save()
