"""Parity contracts for the experimental renderer, not a global Django patch."""
import gc
import weakref

import owned_render_release
import pytest
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.template.context import ContextDict
from django.test import RequestFactory
from django.utils.translation import override


class SyntheticProcessorError(RuntimeError):
    pass


def synthetic_processor(request):
    if request.path == '/processor-failure/':
        raise SyntheticProcessorError('Synthetic processor failure')
    return {'collision': 'processor', 'processor_only': 'processor-present'}


@pytest.fixture
def render_engine(settings):
    templates = {
        'base.html': 'base[{% block body %}{% endblock %}]',
        'page.html': (
            '{% extends "base.html" %}{% load i18n %}{% block body %}'
            '{{ collision }}|{{ processor_only|default:"absent" }}|'
            '{{ request.path|default:"no-request" }}|{{ unsafe }}|'
            '{% include "child.html" with value=unsafe only %}|'
            '{% get_current_language as language %}{{ language }}{% endblock %}'
        ),
        'child.html': '{{ value }}:{{ collision|default:"isolated" }}',
        'missing-include.html': '{% include "absent-child.html" %}',
    }
    settings.TEMPLATES = [{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'NAME': 'owned-contract',
        'APP_DIRS': False,
        'OPTIONS': {
            'debug': True,
            'loaders': [('django.template.loaders.locmem.Loader', templates)],
            'context_processors': [
                'django.template.context_processors.request',
                __name__ + '.synthetic_processor',
            ],
        },
    }]
    return settings


def observe_contexts(monkeypatch):
    contexts = []
    original = owned_render_release.make_context

    def capture(*args, **kwargs):
        value = original(*args, **kwargs)
        contexts.append(value)
        return value

    monkeypatch.setattr(owned_render_release, 'make_context', capture)
    return contexts


def assert_owned_links_released(contexts):
    assert len(contexts) == 1
    assert all(layer.context is None for layer in contexts[0].dicts
               if isinstance(layer, ContextDict))


@pytest.mark.parametrize('with_request', [False, True])
@pytest.mark.parametrize('autoescape', [False, True])
@pytest.mark.parametrize('language', ['es', 'en'])
def test_owned_render_matches_precedence_includes_escape_and_language(
    render_engine, monkeypatch, with_request, autoescape, language,
):
    render_engine.TEMPLATES[0]['OPTIONS']['autoescape'] = autoescape
    request = RequestFactory().get('/synthetic/') if with_request else None
    unsafe = '<b>Synthetic</b>'
    context = {'collision': 'caller', 'unsafe': unsafe}
    original_context = context.copy()
    with override(language):
        native = render(request, 'page.html', context, status=202,
                        content_type='text/plain; charset=utf-8', using='owned-contract')
        contexts = observe_contexts(monkeypatch)
        candidate = owned_render_release.render_owned_context(
            request, 'page.html', context, status=202,
            content_type='text/plain; charset=utf-8', using='owned-contract',
        )
    assert candidate.content == native.content
    assert dict(candidate.headers) == dict(native.headers)
    assert candidate.status_code == native.status_code == 202
    escaped = '&lt;b&gt;Synthetic&lt;/b&gt;' if autoescape else unsafe
    processor = 'processor-present' if with_request else 'absent'
    path = '/synthetic/' if with_request else 'no-request'
    assert candidate.content.decode() == (
        f'base[caller|{processor}|{path}|{escaped}|{escaped}:isolated|{language}]'
    )
    assert context == original_context
    assert contexts[0].get('collision') == 'caller'
    assert_owned_links_released(contexts)


@pytest.mark.parametrize('template,path,error', [
    ('missing-include.html', '/synthetic/', TemplateDoesNotExist),
    ('page.html', '/processor-failure/', SyntheticProcessorError),
])
def test_owned_render_propagates_native_failure_and_releases_links(
    render_engine, monkeypatch, template, path, error,
):
    request = RequestFactory().get(path)
    with pytest.raises(error) as native:
        render(request, template, {'collision': 'caller'}, using='owned-contract')
    contexts = observe_contexts(monkeypatch)
    with pytest.raises(error) as candidate:
        owned_render_release.render_owned_context(
            request, template, {'collision': 'caller'}, using='owned-contract',
        )
    assert str(candidate.value) == str(native.value)
    assert candidate.value.__traceback__ is not None
    if error is TemplateDoesNotExist:
        assert candidate.value.backend.name == native.value.backend.name == 'owned-contract'
    assert_owned_links_released(contexts)


@pytest.mark.parametrize('with_request', [False, True])
def test_owned_context_dies_before_cyclic_gc(render_engine, monkeypatch, with_request):
    refs = []
    original = owned_render_release.make_context

    def capture(*args, **kwargs):
        context = original(*args, **kwargs)
        refs.append(weakref.ref(context))
        return context

    monkeypatch.setattr(owned_render_release, 'make_context', capture)
    request = RequestFactory().get('/synthetic/') if with_request else None
    enabled = gc.isenabled()
    gc.disable()
    try:
        response = owned_render_release.render_owned_context(
            request, 'page.html', {'collision': 'caller', 'unsafe': 'Synthetic'},
            using='owned-contract',
        )
        assert response.status_code == 200
        assert len(refs) == 1 and refs[0]() is None
    finally:
        if enabled:
            gc.enable()


def test_invalid_context_keeps_native_type_error(render_engine):
    for renderer in (render, owned_render_release.render_owned_context):
        with pytest.raises(TypeError, match='context must be a dict rather than list'):
            renderer(None, 'page.html', [], using='owned-contract')


def test_missing_top_level_template_keeps_native_error(render_engine):
    failures = []
    for renderer in (render, owned_render_release.render_owned_context):
        with pytest.raises(TemplateDoesNotExist) as failure:
            renderer(None, 'absent-top.html', {}, using='owned-contract')
        failures.append(failure.value)
    assert str(failures[0]) == str(failures[1]) == 'absent-top.html'


def test_unknown_backend_is_explicitly_out_of_prototype_scope(monkeypatch):
    class UnsupportedTemplate:
        def render(self, *args, **kwargs):
            raise AssertionError('Unsupported backend must not be partially rendered')

    monkeypatch.setattr(owned_render_release.loader, 'get_template',
                        lambda *args, **kwargs: UnsupportedTemplate())
    with pytest.raises(TypeError, match='only exact Django template backend'):
        owned_render_release.render_owned_context(None, 'synthetic.html', {})
