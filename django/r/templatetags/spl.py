__author__ = 'rfujara'

from django import template

register = template.Library()


@register.filter
def spl2url(value):
    return value.replace("\n", "%0A")
