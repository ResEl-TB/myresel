from django import template
from campus.models.clubs_models import StudentOrganisation
from django.core.exceptions import ObjectDoesNotExist

from dateutil.relativedelta import relativedelta

register = template.Library()

@register.filter
def next_month(date):
    return date + relativedelta(months=+1)

@register.filter
def previous_month(date):
    return date + relativedelta(months=-1)

@register.filter
def get_clubs(clubs):
    clubs = clubs.split(";")
    clubs_name = []
    for club in clubs:
        try:
            clubs_name += [StudentOrganisation.get(cn=club).name]
        except ObjectDoesNotExist:
            pass
    return clubs_name
