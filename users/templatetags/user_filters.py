# users/templatetags/user_filters.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key.
    """
    if not dictionary:
        return None

    return dictionary.get(str(key))