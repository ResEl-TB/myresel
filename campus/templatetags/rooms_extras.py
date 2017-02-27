from django import template

from dateutil.relativedelta import relativedelta

register = template.Library()

@register.filter
def next_month(date):
    return date + relativedelta(months=+1)

@register.filter
def previous_month(date):
    return date + relativedelta(months=-1)