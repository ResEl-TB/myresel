from django import template

register = template.Library()

@register.filter
def remove_unwanted_strings(value):
    return value.replace("-","")
