# coding: utf-8
import json
import uuid
import re
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.db import models

from fonctions import generic
from fonctions import ldap
import ldapback
from ldapback.models.fields import LdapCharField, LdapPasswordField, LdapNtPasswordField, LdapListField, \
    LdapDatetimeField, LdapBooleanField
from myresel.settings import LDAP_DN_PEOPLE
from myresel.settings_local import LDAP_DN_GROUPS, LDAP_DN_ROOMS


class LdapUser(ldapback.models.LdapModel):
    """
    The class having all the element for a user
    """
    base_dn = LDAP_DN_PEOPLE
    #object_classes = ['genericPerson', 'enstbPerson', 'reselPerson', 'maiselPerson', 'aePerson', 'mailPerson']

    # genericPerson
    uid = LdapCharField(db_column='uid', object_classes=['genericPerson'], pk=True)
    first_name = LdapCharField(db_column='firstname', object_classes=['genericPerson'])
    last_name = LdapCharField(db_column='lastname', object_classes=['genericPerson'])
    display_name = LdapCharField(db_column='displayname', object_classes=['genericPerson'])
    user_password = LdapPasswordField(db_column='userpassword', object_classes=['genericPerson'])
    nt_password = LdapNtPasswordField(db_column='ntpassword', object_classes=['genericPerson'])
    postal_address = LdapCharField(db_column='postaladdress', object_classes=['genericPerson'])

    # Ldap Groups
    groups = LdapListField(db_column='memberOf')

    # reselPerson
    mail = LdapCharField(db_column='mail', object_classes=['reselPerson'])
    mobile = LdapCharField(db_column='telephoneNumber', object_classes=['reselPerson'])
    inscr_date = LdapDatetimeField(db_column='dateinscr', object_classes=['reselPerson'])
    cotiz = LdapListField(db_column='cotiz', object_classes=['reselPerson'])
    end_cotiz = LdapDatetimeField(db_column='endinternet', object_classes=['reselPerson'])
    campus = LdapCharField(db_column='campus', object_classes=['reselPerson'])
    birth_place = LdapCharField(db_column='birthplace', object_classes=['reselPerson'])
    birth_country = LdapCharField(db_column='birthcountry', object_classes=['reselPerson'])
    freeform_birth_date = LdapCharField(db_column='freeformbirthdate', object_classes=['reselPerson'])

    # maiselPerson
    building = LdapCharField(db_column='batiment', object_classes=['maiselPerson'])
    room_number = LdapCharField(db_column='roomnumber', object_classes=['reselPerson'])
    # TODO: coupure

    # enstPerson
    promo = LdapCharField(db_column='promo', object_classes=['enstbPerson'])
    anneeScolaire = LdapCharField(db_column='anneeScolaire', object_classes=['enstbPerson'])
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
    mode_paiement = LdapCharField(db_column='aeModePaiement', object_classes=['aePerson'])
    ae_admin = LdapBooleanField(db_column='aeAdmin', object_classes=['aePerson'])
    # TODO: other fields

    # mailPerson
    mail_local_address = LdapListField(db_column='mailLocalAddress', object_classes=['mailPerson'])
    mail_dir = LdapCharField(db_column='mailDir', object_classes=['mailPerson'])
    home_directory = LdapCharField(db_column='homeDirectory', object_classes=['mailPerson'])
    mail_routing_address = LdapCharField(db_column='mailRoutingAddress', object_classes=['mailPerson'])
    mail_del_date = LdapDatetimeField(db_column='mailDelDate', object_classes=['mailPerson'])

    # maiselEmployee
    employee_type = LdapCharField(db_column='maiselEmployeeType', object_classes=['maiselEmployee'])

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
        now = datetime.now().astimezone()
        if self.end_cotiz < now:
            return 'danger'
        elif self.end_cotiz < (now + timedelta(days=25)):
            return 'warning'
        else:
            return 'success'

    @staticmethod
    def generate_address(campus, building, room):
        campus = campus.lower()
        if campus == 'brest':
            return ("Bâtiment {}, Chambre {}\nMaisel IMT Atlantique\n655 avenue du Technopôle\n"
                    "29280 Plouzané").format(building, room)
        if campus == 'rennes':
            if building == 'C1':
                return "Chambre {}\n1 rue de la Châtaigneraie\n35510 Cesson-Sévigné".format(room)
            return "Logement {}\n3 rue de la Châtaigneraie\n35510 Cesson-Sévigné".format(room)
        if campus == 'nantes':
            if building == 'PC':
                return "Chambre {}\n13 rue Pitre Chevalier\n44000 Nantes".format(room)
            numbers = {'N': 2, 'P': 4, 'Q': 6, 'R': 5, 'S': 7, 'T': 9}
            if building in numbers:
                return ("Bâtiment {}, Chambre {}\nMDE IMT Atlantique\n{} allée Jean Baptiste "
                        "Fourier\n44300 Nantes").format(building, room, numbers[building])
        return "Adresse inconnue"

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
        Tells whether the user is allowed to moderate campus emails
        :return: bool
        """
        return LdapGroup.get(pk='campusmodo').is_member(self.uid)

    def is_staff(self):
        """
        Tells if the user is part of the ResEl staff
        :return: bool
        """
        if ldap.search(settings.LDAP_OU_ADMIN, '(&(uid=%s))' % self.uid):
            return True
        return False


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

    def get_members(self):
        members = []
        # pylint: disable=not-an-iterable
        for member in self.members:
            m = re.search(r'^uid=(\w+)', member)
            members.append(LdapUser.get(uid=m.group(1)))
        return members

    def add_member(self, pk):
        # pylint: disable=unsupported-membership-test
        if pk not in self.members:
            # pylint: disable=unsupported-membership-test,no-member
            self.members.append(pk)
            self.save()

    def remove_member(self, uid):
        uid = "uid="+uid+",ou=people,dc=maisel,dc=enst-bretagne,dc=fr"
        # pylint: disable=unsupported-membership-test
        if uid in self.members and len(self.members) > 1: #Avoid error if there is no member
            # pylint: disable=unsupported-membership-test,no-member
            self.members.remove(uid)
            self.save()


class LdapRoom(ldapback.models.LdapModel):

    @staticmethod
    def exists(room, building):
        """Permet de chercher dans le LDAP si une chambre existe

        Returns:
            bool -- False si la chambre n'existe pas, le réstulat de la
            requête LDAP sinon.
        """

        base_dn = LDAP_DN_ROOMS
        searchPattern = '(&(roomNumber=' + str(room) + \
            ')(batiment=' + str(building) + '))'
        return ldap.search(base_dn,  searchPattern)
