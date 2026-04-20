from django import template

register = template.Library()


@register.filter
def dict_value(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return getattr(d, key, "")
