"""Bounded post-response WSGI object graph; no client response/context capture."""
import gc
import hashlib
import json
import os
import weakref
from collections import Counter
from pathlib import Path

import pytest
from django.core.handlers.wsgi import WSGIHandler
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation, publication_state
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_wsgi_object_lifetime(request, monkeypatch):
    if not any(str(x).split('::')[0] == 'tests/test_owned_wsgi_object_lifetime.py' for x in request.config.args):
        pytest.skip('Explicit owned WSGI lifetime inspection only')
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'].startswith('web-modelos-ci-pg-')
    request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    handler = WSGIHandler()
    factory = RequestFactory()
    observed = []
    original = public_validation.PublicationContext.__init__
    def tracked(context, *args, **kwargs):
        original(context, *args, **kwargs)
        observed.append(('context', weakref.ref(context)))
        for row in context.rows:
            observed.append(('listing', weakref.ref(row)))
            if row.approved_revision:
                observed.append(('revision', weakref.ref(row.approved_revision)))
    monkeypatch.setattr(public_validation.PublicationContext, '__init__', tracked)
    def call(route):
        status = []
        def start_response(value, headers, exc_info=None):
            status.append((value, dict(headers)))
        response = handler(factory.get(route).environ, start_response)
        try:
            assert status[0][0].startswith('200 ')
            assert status[0][1]['Cache-Control'] == 'no-store'
            assert not hasattr(response, 'client') and not hasattr(response, 'json')
            return hashlib.sha256(b''.join(response)).hexdigest()
        finally:
            response.close()
    output = []
    flags, enabled = gc.get_debug(), gc.isenabled()
    assert not gc.garbage
    try:
        for route in ['/es/', '/en/?q=synthetic']:
            expected = call(route)
            observed.clear()
            gc.collect()
            gc.disable()
            gc.set_debug(flags | gc.DEBUG_SAVEALL)
            assert call(route) == expected
            def inspect_cycles():
                paths = Counter()
                for kind, ref in observed:
                    parent = ref()
                    if parent is None:
                        continue
                    for relation, queryset in getattr(parent, '_prefetched_objects_cache', {}).items():
                        if getattr(queryset, '_hints', {}).get('instance') is parent:
                            paths[(kind, relation, 'prefetch_cache -> QuerySet._hints.instance -> same_parent')] += 1
                        for child in getattr(queryset, '_result_cache', None) or []:
                            for field, target in child._state.fields_cache.items():
                                if target is parent:
                                    paths[(kind, relation, 'prefetch_cache -> QuerySet._result_cache -> child.fields_cache.'+field+' -> same_parent')] += 1
                    for relation in ['_pv_photos', '_pv_rates']:
                        for child in getattr(parent, relation, []):
                            for field, target in child._state.fields_cache.items():
                                if target is parent:
                                    paths[(kind, relation, 'list -> child.fields_cache.'+field+' -> same_parent')] += 1
                return [{'parent_kind':kind,'relation':relation,'path':path,'count':count}
                        for (kind,relation,path),count in paths.items()]
            identity_cycles = inspect_cycles()
            assert identity_cycles, 'No identity cycle demonstrated'
            before = Counter(kind for kind, ref in observed if ref() is not None)
            collected = gc.collect()
            after = Counter(kind for kind, ref in observed if ref() is not None)
            objects = list(gc.garbage)
            ids = {id(obj) for obj in objects}
            def typename(obj):
                return type(obj).__module__ + '.' + type(obj).__qualname__
            types = Counter(typename(obj) for obj in objects)
            edges = Counter()
            for obj in objects:
                for other in gc.get_referents(obj):
                    if id(other) in ids:
                        edges[(typename(obj), typename(other))] += 1
            output.append({'route':route,'native_wsgi_without_test_client':True,
                'identity_cycles':identity_cycles,'tracked_alive_before_gc':dict(before),'tracked_alive_after_saveall_gc':dict(after),
                'collected_total':collected,'saved_objects':len(objects),
                'types':types.most_common(25),
                'internal_type_edges':[{'source':a,'target':b,'count':n} for (a,b),n in edges.most_common(35)],
                'limits':'DEBUG_SAVEALL deliberately retains unreachable objects, so weakrefs and saved-object counts must not be treated as persistent leaks. Type edges are not SCC proof. No values/SQL/params exported; no timings.'})
            gc.garbage.clear()
            del objects, ids, obj
            if 'other' in locals():
                del other
            observed.clear()
            gc.set_debug(flags)
            gc.collect()
            if enabled:
                gc.enable()
        assert len(output)==2
    finally:
        gc.set_debug(flags)
        gc.garbage.clear()
        if enabled:
            gc.enable()
        else:
            gc.disable()
    assert gc.get_debug()==flags and gc.isenabled()==enabled
    out=Path(request.config.getoption('--gate-timings-output')).parent
    (out/'wsgi-lifetime.json').write_text(json.dumps(output,indent=2)+'\n')
