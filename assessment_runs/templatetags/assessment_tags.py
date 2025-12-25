from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def to_json(value):
    return json.dumps(value)
