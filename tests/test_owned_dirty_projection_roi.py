"""Owned WSGI diagnostic: native A/A controls and exact dirty-row projection prototype."""
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
from owned_dirty_projection import build_dirty_projection_prototype
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_dirty_projection_roi(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_dirty_projection_roi.py'
               for x in request.config.args):
        pytest.skip('Explicit owned WSGI diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    request.getfixturevalue('directory')
    dataset = populate(10000)
    target = Listing.objects.select_related('approved_revision').get(pk=dataset['sample_ids'][0])
    Revision.objects.create(listing=target, manager_version=target.approved_revision.manager_version)
    publication_state.refresh_all()
    publication_state.mark([target.pk])  # Controlled pending marker, no writer optimization.
    marks = list(PublicationDirty.objects.values_list('pk', 'generation'))
    assert len(marks) == 1
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    assert gc.isenabled() and gc.get_debug() == 0 and not gc.garbage
    gc_flags = gc.isenabled(), gc.get_debug(), gc.get_threshold()
    native_state_page = publication_state._state_page
    proposed_state_page = build_dirty_projection_prototype()
    observed_modes = dict.fromkeys(['A', 'B', 'C'], 0)

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
                implementation = proposed_state_page if arm == 'C' else native_state_page

                def observed_page(*args, **kwargs):
                    page = implementation(*args, **kwargs)
                    assert args[3]['population'] == ('projection' if arm == 'C' else 'native_query')
                    observed_modes[arm] += 1
                    return page

                monkeypatch.setattr(publication_state, '_state_page', observed_page)
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
    assert observed_modes == dict.fromkeys(['A', 'B', 'C'], 132)
    assert list(PublicationDirty.objects.values_list('pk', 'generation')) == marks
    comparisons = []
    for route in routes:
        selected = [row for row in samples if row['route'] == route]
        for arm in ['A', 'B', 'C']:
            assert len({row['sql'] for row in selected if row['arm'] == arm}) == 1
        means = {arm: {metric: statistics.mean(row[metric] for row in selected if row['arm'] == arm)
                       for metric in ['wall', 'cpu']} for arm in ['A', 'B', 'C']}
        stable = all(abs(means['A'][metric] - means['B'][metric]) /
                     statistics.mean([means['A'][metric], means['B'][metric]]) <= .10
                     for metric in ['wall', 'cpu'])
        relative = {metric: means['C'][metric] /
                    statistics.mean([means['A'][metric], means['B'][metric]])
                    for metric in ['wall', 'cpu']}
        wall_block_gains = []
        for block in range(3):
            base = statistics.mean(row['wall'] for row in selected
                                   if row['block'] == block and row['arm'] in ['A', 'B'])
            candidate = statistics.mean(row['wall'] for row in selected
                                        if row['block'] == block and row['arm'] == 'C')
            wall_block_gains.append(candidate <= base)
        eligible = stable and relative['cpu'] <= 1.05 and relative['wall'] <= .90 and sum(wall_block_gains) >= 2
        comparisons.append(dict(route=route, means=means, control_stable=stable,
                                candidate_to_reference=relative, wall_nonregression_blocks=wall_block_gains,
                                eligible_for_integration=eligible))
    result = dict(samples=samples, preparation=preparation, comparisons=comparisons,
                  eligible_for_integration=all(row['eligible_for_integration'] for row in comparisons),
                  limits='Test-only WSGI, no TCP/Gunicorn/concurrency/dirty writes or SLO acceptance. '
                         'A/B identical native code; C clean projection UNION fresh validated dirty rows. '
                         'Normal GC inside requests; explicit collection before warmup only. '
                         'Controlled dirty1 throughout, no real writer/refresh schedule. '
                         'Control <=10% wall/CPU disagreement each route; candidate >=10% mean wall '
                         'savings both routes, CPU regression <=5%, wall nonregression >=2/3 blocks. '
                         'PASS means functional parity and diagnostic completion, not demonstrated ROI.')
    (out / 'dirty-projection-roi.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('owned_dirty_projection_roi', json.dumps({
        'reads': len(samples), 'eligible': result['eligible_for_integration'],
    }))
