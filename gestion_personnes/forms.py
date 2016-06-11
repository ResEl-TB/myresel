from django import forms
from fonctions.ldap import search_ecole

class InscriptionForm(forms.Form):

    def __init__(self, uid):
        super().__init__()
        if len(search_ecole(uid)) == 0:
            # Utilisateur non présent dans le LDAP école
            self.nom = forms.CharField()
            self.prenom = forms.CharField()
            self.mail = forms.EmailField()
        else:
            # Utilisateur existant dans le LDAP école
            user = search_ecole(uid)[0]
            self.nom = forms.CharField(initial = user.cn[0].split(' ')[0])
            self.prenom = forms.CharField(initial = user.cn[0].split(' ')[1])
            self.mail = forms.EmailField(initial = user.mail[0])

    mot_de_passe = forms.CharField(widget = forms.PasswordInput)