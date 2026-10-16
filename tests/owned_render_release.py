"""Experimental owned-context renderer; never installed by application imports."""
from django.http import HttpResponse
from django.template import loader
from django.template.backends.django import Template as DjangoTemplate
from django.template.backends.django import reraise
from django.template.context import ContextDict, make_context


def render_owned_context(request, template_name, context=None, content_type=None, status=None, using=None):
    template = loader.get_template(template_name, using=using)
    if type(template) is not DjangoTemplate:
        raise TypeError('Prototype supports only exact Django template backend')
    owned = make_context(context, request, autoescape=template.backend.engine.autoescape)
    try:
        try:
            content = template.template.render(owned)
        except loader.TemplateDoesNotExist as exc:
            reraise(exc, template.backend)
        return HttpResponse(content, content_type, status)
    finally:
        # Leave original input dictionaries untouched. Only request-owned push
        # layers have this exact context backlink, after synchronous rendering.
        for layer in owned.dicts:
            if isinstance(layer, ContextDict) and layer.context is owned:
                layer.context = None
