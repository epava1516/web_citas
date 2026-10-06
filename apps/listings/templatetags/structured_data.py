"""Inert JSON-LD with HTML delimiters escaped before marking serialization safe."""

import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def json_ld(value):
    content = json.dumps(value, cls=DjangoJSONEncoder).translate(
        {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"}
    )
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(content))
