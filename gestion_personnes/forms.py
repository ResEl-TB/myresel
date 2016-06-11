from django import forms
from fonctions.ldap import search_ecole

class InscriptionForm(forms.Form):
    nom = forms.CharField()
    prenom = forms.CharField()
    mail = forms.EmailField()
    mot_de_passe = forms.CharField(widget = forms.PasswordInput)

    def __init__(self, uid):
        super().__init__()
        if len(search_ecole(uid)) != 0:
            # Utilisateur présent dans le LDAP école
            user = search_ecole(uid)[0]
            self.nom = forms.CharField(initial = user.cn[0].split(' ')[0])
            self.prenom = forms.CharField(initial = user.cn[0].split(' ')[1])
            self.mail = forms.EmailField(initial = user.mail[0])    