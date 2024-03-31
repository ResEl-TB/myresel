from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    CAPTCHA_ANSWER = ("Paul Friedel", "Paul Fridel", "Fridel", "Friedel", "Fiedel",
                      "Christophe Lerouge", "Lerouge")

    nom = forms.CharField(
        label=_("Votre nom"), widget=forms.TextInput(attrs={"class": "form-control"})
    )
    chambre = forms.CharField(
        label=_("Votre chambre"),
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": _("Bâtiment ET chambre"), "class": "form-control"}
        ),
    )
    mail = forms.EmailField(
        label=_("Votre adresse mail"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    demande = forms.CharField(
        label=_("Votre message"),
        widget=forms.Textarea(attrs={"class": "form-control", "style": "resize:none;"}),
    )
    uid = forms.CharField(widget=forms.HiddenInput(), required=False)
    captcha = forms.CharField(
        label=_("Quel est le nom du directeur d'IMT Atlantique (captcha) ?"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def clean_captcha(self):
        def format_captcha(value):
            value = value.strip().lower().replace(" ", "")
            return "".join(sorted(value))

        captcha = format_captcha(self.cleaned_data["captcha"])
        captcha_answers = [format_captcha(c) for c in self.CAPTCHA_ANSWER]

        if captcha not in captcha_answers:
            raise forms.ValidationError(
                _("Mauvaise réponse au captcha"), code="WRONG CAPTCHA"
            )
        return captcha
