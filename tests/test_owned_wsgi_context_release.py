"""Bounded post-response WSGI object graph; no client response/context capture."""
import gc
import hashlib
import json
import os
import weakref
from collections import Counter, deque
from pathlib import Path

import pytest
from django.core.handlers.wsgi import WSGIHandler
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from owned_render_release import render_owned_context
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, public_validation, publication_state
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_wsgi_context_release(request, monkeypatch):
    if not any(str(x).split('::')[0] == 'tests/test_owned_wsgi_context_release.py' for x in request.config.args):
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
    native_digests = {route:call(route) for route in ['/es/', '/en/?q=synthetic']}
    original_render = render_owned_context
    closed = []
    reverse_cycles = []
    def render_with_release(*args, **kwargs):
        response = original_render(*args, **kwargs)
        page = args[2]['page']
        rows = list(page.object_list)
        def release():
            # Prototype only: drop outgoing cache/list references after full response consumption.
            count = 0
            for row in rows:
                person = row._state.fields_cache.get('person')
                if person is not None and person._state.fields_cache.get('listing') is row:
                    count += 1
                    del person._state.fields_cache['listing']
                revision = row.approved_revision
                if revision is not None:
                    getattr(revision, '_prefetched_objects_cache', {}).clear()
                    for name in ['categories', 'services', 'travel_areas', 'rates', 'photos']:
                        revision.__dict__.pop('_pv_' + name, None)
            reverse_cycles.append(count)
            rows.clear()
            closed.append(True)
        response._resource_closers.append(release)
        return response
    monkeypatch.setattr(discovery, 'render', render_with_release)
    output = []
    flags, enabled = gc.get_debug(), gc.isenabled()
    assert not gc.garbage
    try:
        for route in ['/es/', '/en/?q=synthetic']:
            expected = call(route)
            assert expected == native_digests[route]
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
            assert not identity_cycles, identity_cycles
            before = Counter(kind for kind, ref in observed if ref() is not None)
            def residual_path():
                root = next((ref() for kind, ref in observed if kind=='listing' and ref() is not None), None)
                if root is None:
                    return {'found':False,'reason':'root already released'}
                def label(obj):
                    return type(obj).__module__+'.'+type(obj).__qualname__
                queue = deque([(root,[label(root)])])
                seen = {id(root)}
                while queue and len(seen)<20000:
                    obj, path = queue.popleft()
                    if len(path)>14:
                        continue
                    for child in gc.get_referents(obj):
                        if child is root:
                            return {'found':True,'types':path+[label(root)],'visited':len(seen)}
                        allowed = isinstance(child,(dict,list,tuple,set,frozenset)) or label(child).startswith(('apps.','django.db.models.'))
                        if allowed and not isinstance(child,type) and id(child) not in seen:
                            seen.add(id(child))
                            queue.append((child,path+[label(child)]))
                return {'found':False,'visited':len(seen),'truncated':bool(queue)}
            out = Path(request.config.getoption('--gate-timings-output')).parent
            (out/'residual-before-assert.json').write_text(json.dumps({
                'route':route,'alive':dict(before),'closed_callbacks':len(closed),
                'reverse_identity_counts':reverse_cycles,'cycle':residual_path()},indent=2)+'\n')
            assert not before, before
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
    assert len(closed)==4
    assert reverse_cycles == [24, 24, 24, 24], reverse_cycles
    out=Path(request.config.getoption('--gate-timings-output')).parent
    (out/'wsgi-context-release.json').write_text(json.dumps({'routes':output,'reverse_identity_cycles_before_removal':reverse_cycles},indent=2)+'\n')
