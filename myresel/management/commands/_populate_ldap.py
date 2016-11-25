# coding: utf-8

from datetime import datetime, timedelta
from itertools import product

from gestion_personnes.models import LdapUser

now = datetime.now()
month_later = now + timedelta(days=31)
previous_month = now - timedelta(days=31)
current_year = now.year
previous_year = now.year - 1
next_year = now.year + 1

# Tous les éléments pouvant rentrer dans la constitution d'une clé primaire ne se retrouveront pas
# dans le produit cartésien des ensembles des possibles
# On distingue donc deux ensembles : les ensembles identifiants et les ensembles attributs

# Ensembles Attributs

# reselPerson
potential_is_reselPerson = [False, True]  # Bool
potential_inscr_date = [previous_month, now]  # Date
potential_cotiz = [str(next_year), str(previous_year)]  # String ...... ????????????
potential_end_cotiz = [previous_month, month_later]  # Date
potential_campus = ["Brest"]  # String

# maiselPerson
potential_is_maiselPerson = [False, True]  # Bool

# enstbPerson
potential_is_enstbPerson = [False, True]  # Bool
potential_promo = [str(next_year)]  # String
potential_anneeScolaire = ["{}-{}".format(current_year, next_year)]  # String
potential_option = ["ESH"]  # String ...... ??????????
potential_formation = ["FIP", "FIG"]  # String
potential_photo_file = [""]  # String
potential_uid_godchildren = [[]]  # List
potential_uid_godparents = [[]]  # List
potential_origin = ["Sealand"]  # String

# aePerson
potential_is_aePerson = [False, True]  # Bool
potential_ae_cotiz = [str(previous_year), str(next_year)]  # String
potential_ae_nature = ["CB", "Liquide"]  # String

# mailPerson
potential_is_mailPerson = [False, True]  # Bool

cartesian_product = product(
    potential_is_reselPerson,
    potential_inscr_date,
    potential_cotiz,
    potential_end_cotiz,
    potential_campus,
    potential_is_maiselPerson,
    potential_is_enstbPerson,
    potential_promo,
    potential_anneeScolaire,
    potential_option,
    potential_formation,
    potential_photo_file,
    potential_uid_godchildren,
    potential_uid_godparents,
    potential_origin,
    potential_is_aePerson,
    potential_ae_cotiz,
    potential_ae_nature,
    potential_is_mailPerson
)

# Donne la correspondance entre la case du tableau cartesian_product et le champs pour les champs attributs
# Seuls les attributs rentrent dans le dictionnaire
link_dict = {
    "is_reselPerson": 0,
    "inscr_date": 1,
    "cotiz": 2,
    "end_cotiz": 3,
    "campus": 4,
    "is_maiselPerson": 5,
    "is_enstbPerson": 6,
    "promo": 7,
    "anneeScolaire": 8,
    "option": 9,
    "formation": 10,
    "photo_file": 11,
    "uid_godchildren": 12,
    "uid_godparents": 13,
    "origin": 14,
    "is_aePerson": 15,
    "ae_cotiz": 16,
    "ae_nature": 17,
    "is_mailPerson": 18
}

cartesian_product = list(cartesian_product)
sample_number = len(cartesian_product)  # Nombre de possibilités générées

# Ensembles Identifiants
potential_first_name = [hex(i) for i in range(sample_number)]  # String
potential_last_name = ["{}last".format(hex(i)) for i in range(sample_number)]  # String
potential_uid = [
    potential_first_name[i][0] + potential_last_name[i]
    [0:max(len(potential_last_name[i]) - 1, 7)] for i in range(sample_number)
]  # String
potential_user_password = ["#ldap%{}".format(potential_uid[i]) for i in range(sample_number)]  # String
potential_nt_password = ["{}#ldap%".format(potential_uid[i]) for i in range(sample_number)]  # String
potential_display_name = [
     "{} {}".format(potential_first_name[i], potential_last_name[i])
     for i in range(sample_number)
]  # String
# potential_postal_address générée lors de la création de l'utilisateur


# maiselPerson
potential_building = ["I1" for i in range(sample_number)]  # String
potential_room_number = ["220" for i in range(sample_number)]  # String

# enstbPerson
potential_mail = [
    "{}.{}@telecom-bretagne.eu".format(potential_first_name[i], potential_last_name[i])
    for i in range(sample_number)
]  # String
potential_mobile = [
    "336{}{}".format("0" * (8 - len(str(i))), str(i))
    for i in range(sample_number)]  # String

# aePerson
potential_n_adherent = [str(i) for i in range(sample_number)]  # String

# mailPerson
potential_mail_local_address = [
    "{}.{}@resel.fr".format(potential_first_name[i], potential_last_name[i])
    for i in range(sample_number)
]  # String
potential_mail_dir = ["{}/Maildir/".format(potential_uid[i]) for i in range(sample_number)]  # String
potential_home_directory = ["/var/mail/virtual/{}".format(potential_uid[i]) for i in range(sample_number)]  # String

# On remplit maintenant la base de donnée
compteur = 0
for element in cartesian_product:
    user = LdapUser()
    user.object_classes = ["genericPerson"]
    user.uid = potential_uid[compteur]
    user.first_name = potential_first_name[compteur]
    user.last_name = potential_last_name[compteur]
    user.user_password = potential_user_password[compteur]
    user.nt_password = potential_nt_password[compteur]
    user.display_name = potential_display_name[compteur]
    user.postal_address = "655, avenue du technopôle\n29280 PLOUZANE"
    if element[link_dict["is_reselPerson"]]:
        user.object_classes.append("reselPerson")
        user.inscr_date = element[link_dict["inscr_date"]]
        user.cotiz = element[link_dict["cotiz"]]
        user.end_cotiz = element[link_dict["end_cotiz"]]
        user.building = potential_building[compteur]
        user.room_number = potential_room_number[compteur]
    if element[link_dict["is_enstbPerson"]]:
        user.object_classes.append("enstbPerson")
        user.promo = element[link_dict["promo"]]
        user.mail = potential_mail[compteur]
        user.anneeScolaire = element[link_dict["anneeScolaire"]]
        user.mobile = potential_mobile[compteur]
        user.option = element[link_dict["option"]]
        user.formation = element[link_dict["formation"]]
        user.photo_file = element[link_dict["photo_file"]]
        user.uid_godchildren = element[link_dict["uid_godchildren"]]
        user.uid_godparents = element[link_dict["uid_godparents"]]
        user.origin = element[link_dict["origin"]]
    if element[link_dict["is_aePerson"]]:
        user.object_classes.append("aePerson")
        user.ae_cotiz = element[link_dict["ae_cotiz"]]
        user.ae_nature = ae_cotiz = element[link_dict["ae_nature"]]
        user.n_adherent = potential_n_adherent[compteur]
    if element[link_dict["is_mailPerson"]]:
        user.object_classes.append("mailPerson")
        user.mail_local_address = potential_mail_local_address[compteur]
        user.mail_dir = potential_mail_dir[compteur]
        user.home_directory = potential_home_directory[compteur]
    user.save()
