"""Owned WSGI diagnostic: native A/A controls and lifecycle-release prototype."""
import gc
import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from owned_render_release import render_owned_context
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, publication_state
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_wsgi_release_roi(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_wsgi_release_roi.py'
               for x in request.config.args):
        pytest.skip('Explicit owned WSGI diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    assert gc.isenabled() and gc.get_debug() == 0 and not gc.garbage
    gc_flags = gc.isenabled(), gc.get_debug(), gc.get_threshold()
    native_render = discovery.render
    cleanup_counts = []

    def candidate_render(*args, **kwargs):
        response = render_owned_context(*args, **kwargs)
        rows = list(args[2]['page'].object_list)

        def release():
            count = 0
            for row in rows:
                person = row._state.fields_cache.get('person')
                if person is not None and person._state.fields_cache.get('listing') is row:
                    del person._state.fields_cache['listing']
                revision = row.approved_revision
                if revision is not None:
                    getattr(revision, '_prefetched_objects_cache', {}).clear()
                    for name in ['categories', 'services', 'travel_areas', 'rates', 'photos']:
                        revision.__dict__.pop('_pv_' + name, None)
                count += 1
            rows.clear()
            cleanup_counts.append(count)

        response._resource_closers.append(release)
        return response

    handler, factory = WSGIHandler(), RequestFactory()

    def call(route):
        status = []

        def start_response(value, headers, exc_info=None):
            status.append((value, dict(headers)))

        response = handler(factory.get(route).environ, start_response)
        try:
            body = b''.join(response)
        finally:
            response.close()
        assert status[0][0].startswith('200 ')
        assert status[0][1]['Cache-Control'] == 'no-store'
        return body

    routes = ['/es/', '/en/?q=synthetic']
    signatures = {route: hashlib.sha256(call(route)).hexdigest() for route in routes}
    samples, preparation = [], []
    for route in routes:
        for block, order in enumerate([['A', 'B', 'C'], ['B', 'C', 'A'], ['C', 'A', 'B']]):
            for arm in order:
                monkeypatch.setattr(discovery, 'render', candidate_render if arm == 'C' else native_render)
                connection.close()
                gc.collect()  # Equalize prior-arm garbage outside all timed requests.
                for _ in range(6):
                    assert hashlib.sha256(call(route)).hexdigest() == signatures[route]
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid(), (SELECT count(*) FROM pg_prepared_statements)')
                    backend_pid, prepared = cursor.fetchone()
                preparation.append(dict(route=route, block=block, arm=arm,
                                        backend_pid=backend_pid, prepared_statements=prepared))
                for repeat in range(16):
                    observed = {'sql': 0, 'pids': set()}

                    def counted(execute, sql, params, many, context):
                        observed['sql'] += 1
                        observed['pids'].add(context['connection'].connection.info.backend_pid)
                        return execute(sql, params, many, context)

                    before_gc = gc.get_stats()
                    wall, cpu = time.perf_counter(), time.thread_time()
                    with connection.execute_wrapper(counted):
                        body = call(route)
                    wall, cpu = time.perf_counter() - wall, time.thread_time() - cpu
                    assert observed['pids'] == {backend_pid}
                    assert hashlib.sha256(body).hexdigest() == signatures[route]
                    samples.append(dict(route=route, block=block, arm=arm, repeat=repeat,
                                        wall=wall, cpu=cpu, sql=observed['sql'],
                                        gc_collections=[a['collections'] - b['collections']
                                                        for a, b in zip(gc.get_stats(), before_gc, strict=True)]))
    assert len(samples) == 288
    assert gc_flags == (gc.isenabled(), gc.get_debug(), gc.get_threshold())
    assert cleanup_counts == [24] * 132  # 2 routes × 3 candidate arms × (6 warm + 16 measured).
    comparisons = []
    for route in routes:
        selected = [row for row in samples if row['route'] == route]
        assert len({row['sql'] for row in selected}) == 1
        means = {arm: {metric: statistics.mean(row[metric] for row in selected if row['arm'] == arm)
                       for metric in ['wall', 'cpu']} for arm in ['A', 'B', 'C']}
        stable = all(abs(means['A'][metric] - means['B'][metric]) /
                     statistics.mean([means['A'][metric], means['B'][metric]]) <= .10
                     for metric in ['wall', 'cpu'])
        relative = {metric: means['C'][metric] /
                    statistics.mean([means['A'][metric], means['B'][metric]])
                    for metric in ['wall', 'cpu']}
        block_gains = []
        for block in range(3):
            base = statistics.mean(row['cpu'] for row in selected
                                   if row['block'] == block and row['arm'] in ['A', 'B'])
            candidate = statistics.mean(row['cpu'] for row in selected
                                        if row['block'] == block and row['arm'] == 'C')
            block_gains.append(candidate <= base)
        eligible = stable and relative['cpu'] <= .90 and relative['wall'] <= .95 and sum(block_gains) >= 2
        comparisons.append(dict(route=route, means=means, control_stable=stable,
                                candidate_to_reference=relative, cpu_nonregression_blocks=block_gains,
                                eligible_for_integration=eligible))
    result = dict(samples=samples, preparation=preparation, comparisons=comparisons,
                  eligible_for_integration=all(row['eligible_for_integration'] for row in comparisons),
                  limits='Test-only WSGI, no TCP/Gunicorn/concurrency/dirty writes or SLO acceptance. '
                         'A/B identical native code; C owned render plus model-close release. '
                         'Normal GC inside requests; explicit collection before warmup only. '
                         'Control <=10% wall/CPU disagreement each route; candidate >=10% mean CPU '
                         'and >=5% mean wall savings both routes, CPU nonregression >=2/3 blocks. '
                         'PASS means functional parity and diagnostic completion, not demonstrated ROI.')
    (out / 'wsgi-release-roi.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('owned_wsgi_release_roi', json.dumps({
        'reads': len(samples), 'eligible': result['eligible_for_integration'],
    }))
