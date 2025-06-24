# characters/templatetags/inventory_tags.py
from django import template

from shops.utils.economy import get_sell_price

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)


@register.filter
def sell_price_for(item, character):
    return get_sell_price(item, character)