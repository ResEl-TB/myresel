from django import forms
from django.utils.translation import gettext_lazy as _

class ApproveEmployeeForm(forms.Form):
    employee = forms.CharField()
    action = forms.CharField()

    def clean_action(self):
        action = self.cleaned_data['action']
        if action not in ['approve', 'delete', 'suspend']:
            raise forms.ValidationError(message=_("Une erreur est survenue"),
                                        code="WRONG_MAISEL_ACTION")
        return action
