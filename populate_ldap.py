from datetime import datetime, timedelta
from itertools import product
from gestion_personnes.models import LdapUser

now = datetime.now()
month_later = now + timedelta(days = 31)
previous_month = now - timedelta(days = 31)
current_year = now.year
previous_year = now.year - 1
next_year = now.year + 1

#Tous les éléments pouvant rentrer dans la constitution d'une clé primaire ne se retrouveront pas 
#dans le produit cartésien des ensembles des possibles
#On distingue donc deux ensembles : les ensembles identifiants et les ensembles attributs

#Ensembles Attributs

# reselPerson
ensemble_is_reselPerson = [False, True]                         #Bool
ensemble_inscr_date = [previous_month, now]                     #Date
ensemble_cotiz = [str(next_year), str(previous_year)]           #String ...... ????????????
ensemble_end_cotiz = [previous_month, month_later]              #Date
ensemble_campus = ["Brest"]                                     #String

# maiselPerson
ensemble_is_maiselPerson = [False, True]                        #Bool

# enstbPerson
ensemble_is_enstbPerson = [False, True]                         #Bool
ensemble_promo = [str(next_year)]                               #String
ensemble_anneeScolaire = [str(current_year)+"-"+str(next_year)] #String
ensemble_option = ["ESH"]                                       #String ...... ??????????
ensemble_formation = ["FIP", "FIG"]                             #String
ensemble_photo_file = [""]                                      #String
ensemble_uid_godchildren = [[]]                                 #List
ensemble_uid_godparents = [[]]                                  #List
ensemble_origin = ["Sealand"]                                   #String

# aePerson
ensemble_is_aePerson = [False, True]                            #Bool
ensemble_ae_cotiz = [str(previous_year), str(next_year)]        #String
ensemble_ae_nature = ["CB", "Liquide"]                          #String

# mailPerson
ensemble_is_mailPerson = [False, True]                          #Bool

ensemble_produit = product(\
ensemble_is_reselPerson,\
ensemble_inscr_date,\
ensemble_cotiz,\
ensemble_end_cotiz,\
ensemble_campus,\
ensemble_is_maiselPerson,\
ensemble_is_enstbPerson,\
ensemble_promo,\
ensemble_anneeScolaire,\
ensemble_option,\
ensemble_formation,\
ensemble_photo_file,\
ensemble_uid_godchildren,\
ensemble_uid_godparents,\
ensemble_origin,\
ensemble_is_aePerson,\
ensemble_ae_cotiz,\
ensemble_ae_nature,\
ensemble_is_mailPerson\
)

#Donne la correspondance entre la case du tableau ensemble_produit et le champs pour les champs attributs
#Seuls les attributs rentrent dans le dictionnaire
dictionnaire = {\
"is_reselPerson":0,\
"inscr_date":1,\
"cotiz":2,\
"end_cotiz":3,\
"campus":4,\
"is_maiselPerson":5,\
"is_enstbPerson":6,\
"promo":7,\
"anneeScolaire":8,\
"option":9,\
"formation":10,\
"photo_file":11,\
"uid_godchildren":12,\
"uid_godparents":13,\
"origin":14,\
"is_aePerson":15,\
"ae_cotiz":16,\
"ae_nature":17,\
"is_mailPerson":18\
}

ensemble_produit = list(ensemble_produit)
sample_number = len(ensemble_produit) #Nombre de possibilités générées

#Ensembles Identifiants 
ensemble_first_name = [hex(i) for i in range(sample_number)]                #String
ensemble_last_name = [hex(i)+"last" for i in range(sample_number)]      #String
ensemble_uid = [ensemble_first_name[i][0]+ensemble_last_name[i]\
[0:max(len(ensemble_last_name[i]) - 1, 7)] for i in range(sample_number)]   #String
ensemble_user_password = ["#ldap%"+ensemble_uid[i] for i in range(sample_number)]    #String
ensemble_nt_password = [ensemble_uid[i]+"#ldap%" for i in range(sample_number)]      #String
ensemble_display_name = [ensemble_first_name[i] +" "+\
ensemble_last_name[i] for i in range(sample_number)]                        #String
#ensemble_postal_address Générée lors de la création de l'utilisateur


# maiselPerson
ensemble_building = ["I1" for i in range(sample_number) ]                   #String
ensemble_room_number = ["220" for i in range(sample_number) ]               #String

#enstbPerson
ensemble_mail = [ensemble_first_name[i]+"."+ensemble_last_name[i]+\
"@telecom-bretagne.eu" for i in range(sample_number)]                       #String
ensemble_mobile = ["336" + "0"*(8-len(str(i)))+str(i)\
for i in range(sample_number)]                                              #String

#aePerson
ensemble_n_adherent = [str(i) for i in range(sample_number)]                #String

# mailPerson
ensemble_mail_local_address = [ensemble_first_name[i]+"."+\
ensemble_last_name[i]+"@resel.fr" for i in range(sample_number)]            #String
ensemble_mail_dir = ["" for i in range(sample_number)]                      #String
ensemble_home_directory = ["" for i in range(sample_number)]                #String


#On remplit maintenant la base de donnée
compteur = 0
for element in ensemble_produit :
    user = LdapUser()
    user.object_classes = ["genericPerson"]
    user.uid = ensemble_uid[compteur]
    user.first_name = ensemble_first_name[compteur]
    user.last_name = ensemble_last_name[compteur]
    user.user_password = ensemble_user_password[compteur]
    user.nt_password = ensemble_nt_password[compteur]
    user.display_name = ensemble_display_name[compteur]
    user.postal_address = "655, avenue du technopôle\n29280 PLOUZANE"
    if element[dictionnaire["is_reselPerson"]]:
        user.object_classes.append("reselPerson")
        user.inscr_date = element[dictionnaire["inscr_date"]]
        user.cotiz = element[dictionnaire["cotiz"]]
        user.end_cotiz = element[dictionnaire["end_cotiz"]]
        user.building = ensemble_building[compteur]
        user.room_number = ensemble_room_number[compteur]
    if element[dictionnaire["is_enstbPerson"]]:
        user.object_classes.append("enstbPerson")
        user.promo = element[dictionnaire["promo"]]
        user.mail = ensemble_mail[compteur]
        user.anneeScolaire = element[dictionnaire["anneeScolaire"]]
        user.mobile = ensemble_mobile[compteur]
        user.option = element[dictionnaire["option"]]
        user.formation = element[dictionnaire["formation"]]
        user.photo_file = element[dictionnaire["photo_file"]]
        user.uid_godchildren = element[dictionnaire["uid_godchildren"]]
        user.uid_godparents = element[dictionnaire["uid_godparents"]]
        user.origin = element[dictionnaire["origin"]]
    if element[dictionnaire["is_aePerson"]]:
        user.object_classes.append("aePerson")
        user.ae_cotiz = element[dictionnaire["ae_cotiz"]]
        user.ae_nature = ae_cotiz = element[dictionnaire["ae_nature"]]
        user.n_adherent = ensemble_n_adherent[compteur]
    if element[dictionnaire["is_mailPerson"]]:
        user.object_classes.append("mailPerson")
        user.mail_local_address = ensemble_mail_local_address[compteur]
        user.mail_dir = ensemble_mail_dir[compteur]
        user.home_directory = ensemble_home_directory[compteur]
    compteur += 1
print(compteur)


