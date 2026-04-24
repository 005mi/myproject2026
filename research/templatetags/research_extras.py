from django import template
import os

register = template.Library()

@register.filter
def filename(value):
    return os.path.basename(str(value))

@register.filter
def trim(value):
    return value.strip() if value else ""

@register.filter
def split(value, arg):
    return value.split(arg) if value else []
