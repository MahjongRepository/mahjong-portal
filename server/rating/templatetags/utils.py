# -*- coding: utf-8 -*-
from django.template.defaultfilters import stringfilter, urlize
from django.template.defaulttags import register
from django.utils.safestring import mark_safe


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(is_safe=True)
@stringfilter
def urlize_target_blank(value):
    return mark_safe(urlize(value).replace("<a", '<a target="_blank"'))


@register.filter(is_safe=True)
def get_safe_str(value: str):
    return value if value else ""
