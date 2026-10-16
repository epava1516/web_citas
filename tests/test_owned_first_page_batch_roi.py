"""Owned WSGI diagnostic: native A/A controls and bounded first-page hydration batch prototype."""
import gc
import hashlib
import json
import os
import statistics
import time
from datetime import timedelta
from pathlib import Path

import pytest
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from django.utils import timezone
from owned_first_page_batch import build_first_page_batch_prototype
from owned_state_page_before_batch import build_native_reference
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Municipality
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('scenario', ['dirty1', 'offpage_fanout'])
def test_owned_first_page_batch_roi(request, monkeypatch, record_property, scenario):
    if not any(str(x).split('::')[0] == 'tests/test_owned_first_page_batch_roi.py'
               for x in request.config.args):
        pytest.skip('Explicit owned WSGI diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
    fixture_details = {'scenario': scenario}
    if scenario == 'dirty1':
        target = Listing.objects.select_related('approved_revision').get(pk=dataset['sample_ids'][0])
        Revision.objects.create(listing=target, manager_version=target.approved_revision.manager_version)
        pending = [target.pk]
    else:
        ids = list(Listing.objects.filter(status='published').exclude(pk=dataset['sample_ids'][0])
                   .order_by('pk').values_list('pk', flat=True)[:25])
        assert len(ids) == 25
        pending, victim = ids[:24], ids[24]
        now = timezone.now()
        Listing.objects.filter(pk__in=pending).update(published_at=now + timedelta(days=2))
        Listing.objects.filter(pk=victim).update(published_at=now + timedelta(days=1))
        revision = Listing.objects.select_related('approved_revision').get(pk=victim).approved_revision
        city = Municipality.objects.first()
        cities = Municipality.objects.bulk_create([
            Municipality(code=f'owned-roi-fanout-{n}', name=f'Synthetic ROI fanout {n}',
                         province_id=city.province_id, source_id=city.source_id)
            for n in range(128)
        ])
        revision.travel_areas.add(*cities)
        fixture_details.update(pending_count=24, displaced_clean=str(victim), extra_municipalities=128)
    publication_state.refresh_all()
    publication_state.mark(pending)  # Controlled pending markers, no writer optimization.
    marks = list(PublicationDirty.objects.values_list('pk', 'generation'))
    assert len(marks) == len(pending)
    if scenario == 'offpage_fanout':
        for route in ['/es/', '/en/?q=synthetic']:
            response = client.get(route)
            assert response.status_code == 200
            assert {row.pk for row in response.context['page']} == set(pending)
            assert victim not in {row.pk for row in response.context['page']}
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    assert gc.isenabled() and gc.get_debug() == 0 and not gc.garbage
    gc_flags = gc.isenabled(), gc.get_debug(), gc.get_threshold()
    native_state_page = build_native_reference()
    batch_counts = dict(batch_contexts=0, batch_sizes=[], page_reuses=0, missing_selected_fallbacks=0)
    proposed_state_page = build_first_page_batch_prototype(batch_counts)
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
                    assert args[3]['population'] == 'native_query'
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
    assert batch_counts['batch_contexts'] == batch_counts['page_reuses'] == 132
    assert batch_counts['missing_selected_fallbacks'] == 0
    assert max(batch_counts['batch_sizes']) <= 72
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
    result = dict(fixture=fixture_details, samples=samples, preparation=preparation,
                  comparisons=comparisons, batch_counts=batch_counts,
                  eligible_for_integration=all(row['eligible_for_integration'] for row in comparisons),
                  limits='Test-only WSGI, no TCP/Gunicorn/concurrency/dirty writes or SLO acceptance. '
                         'A/B identical native code; C bounded first-page data batching, native count/selection/guards unchanged. '
                         'Normal GC inside requests; explicit collection before warmup only. '
                         'Controlled pending markers throughout, no real writer/refresh schedule. '
                         'Control <=10% wall/CPU disagreement each route; candidate >=10% mean wall '
                         'savings both routes, CPU regression <=5%, wall nonregression >=2/3 blocks. '
                         'PASS means functional parity and diagnostic completion, not demonstrated ROI.')
    (out / 'first-page-batch-roi.json').write_text(json.dumps(result, indent=2) + '\n')
    record_property('owned_first_page_batch_roi', json.dumps({
        'reads': len(samples), 'eligible': result['eligible_for_integration'],
    }))
