"""Current end-to-end phase attribution; no candidate and no capacity verdict."""

import gc
import hashlib
import json
import os
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import pytest
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from django.db.backends.postgresql.base import ServerSideCursor
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog import promotion_paging
from apps.listings import discovery, public_validation, publication_state
from apps.listings.models import PublicationDirty
from scripts.benchmark_owned_backend_cpu import backend_snapshot, owned_backend

pytestmark = pytest.mark.django_db(transaction=True)


class PhaseRecorder:
    def __init__(self):
        self.stack = []
        self.stats = defaultdict(lambda: {'calls': 0, 'wall_inclusive': 0.0, 'cpu_inclusive': 0.0,
                                         'wall_exclusive': 0.0, 'cpu_exclusive': 0.0})
        self.sql_parents = Counter()
        self.fetch_parents = Counter()
        self.context_rows = []
        self.commercial_rows = 0

    @contextmanager
    def span(self, name):
        frame = {'name': name, 'wall_children': 0.0, 'cpu_children': 0.0}
        self.stack.append(frame)
        wall, cpu = time.perf_counter(), time.thread_time()
        try:
            yield
        finally:
            wall, cpu = time.perf_counter() - wall, time.thread_time() - cpu
            assert self.stack.pop() is frame
            row = self.stats[name]
            row['calls'] += 1
            row['wall_inclusive'] += wall
            row['cpu_inclusive'] += cpu
            row['wall_exclusive'] += wall - frame['wall_children']
            row['cpu_exclusive'] += cpu - frame['cpu_children']
            if self.stack:
                self.stack[-1]['wall_children'] += wall
                self.stack[-1]['cpu_children'] += cpu

    def wrapped(self, owner, name, label):
        original = getattr(owner, name)

        @wraps(original)
        def call(*args, **kwargs):
            with self.span(label):
                result = original(*args, **kwargs)
            if label == 'publication_context':
                self.context_rows.append(len(args[0].rows))
            return result

        return call


def test_current_promotional_request_phases(request, settings, monkeypatch, record_property):
    run_id = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR and not connection.in_atomic_block
    policy = (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    assert policy[0] and policy[2] == 0
    settings.PROMOTION_TEST_MODE = True
    folder = settings.BASE_DIR / 'artifacts/local-ci' / run_id
    runner = json.loads((folder / 'runner.json').read_text())
    container = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert container == 'web-modelos-ci-pg-' + run_id
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', container], text=True))[0]
    preparation_started = time.perf_counter()
    dataset = prepare_promotional_load(request, 10000)
    publication_state.refresh_all()
    preparation_seconds = time.perf_counter() - preparation_started
    assert dataset['published'] == 10000 and dataset['promotions']['count'] == 2000
    assert not PublicationDirty.objects.exists()
    client = request.getfixturevalue('directory')

    def read(path):
        response = client.get(path)
        assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
        assert response.wsgi_request._publication_route['route'] == 'state'
        page = response.context['page']
        assert page.paginator.count == 10000 and len(page.object_list) == 24
        labels = tuple(c['sponsorship'] for c in response.context['cards'])
        assert any(labels)
        return (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                tuple(str(row.pk) for row in page.object_list), labels)

    routes = []
    for route, path in [('directory_es', '/es/'), ('search_en', '/en/?q=synthetic')]:
        expected = read(path)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            sql_pid = cursor.fetchone()[0]
        identity = owned_backend(runner, inspection, sql_pid)

        def snapshot():
            value = backend_snapshot(identity)
            sched = list(map(int, Path(f"/proc/{identity['pid']}/schedstat").read_text().split()))
            assert len(sched) == 3 and sched[0] > 0
            return value | {'runtime_ns': sched[0], 'wait_ns': sched[1]}

        def measured_read():
            before = snapshot()
            wall, cpu = time.perf_counter(), time.thread_time()
            signature = read(path)
            wall, cpu = time.perf_counter() - wall, time.thread_time() - cpu
            after = snapshot()
            assert signature == expected and after['runtime_ns'] >= before['runtime_ns']
            return {'wall': wall, 'app_cpu': cpu, 'backend_cpu': (after['runtime_ns'] - before['runtime_ns']) / 1e9,
                    'backend_wait': (after['wait_ns'] - before['wait_ns']) / 1e9,
                    'backend_before': before, 'backend_after': after}

        controls = [measured_read() for _ in range(5)]
        observations = []
        for _ in range(3):
            recorder = PhaseRecorder()
            original_fetch = ServerSideCursor.fetchmany

            def sql(execute, statement, params, many, context):
                assert not many
                recorder.sql_parents[recorder.stack[-1]['name']] += 1
                with recorder.span('sql_execute'):
                    return execute(statement, params, many, context)

            def fetch(cursor, *args, **kwargs):
                parent = recorder.stack[-1]['name']
                recorder.fetch_parents[parent] += 1
                with recorder.span('server_fetchmany'):
                    rows = original_fetch(cursor, *args, **kwargs)
                if parent == 'commercial':
                    recorder.commercial_rows += len(rows)
                return rows

            before = snapshot()
            with monkeypatch.context() as patch, connection.execute_wrapper(sql):
                for owner, name, label in [
                    (publication_state, '_state_page', 'state_page'),
                    (promotion_paging, '_snapshot_order_population', 'commercial'),
                    (public_validation.PublicationContext, '__init__', 'publication_context'),
                    (public_validation, 'read_publication_values', 'context_hydration'),
                    (publication_state, 'publicly_visible', 'page_guard'),
                    (discovery.PagePresentation, '__init__', 'presentation_init'),
                    (discovery.PagePresentation, 'describe', 'presentation_describe'),
                    (discovery.PagePresentation, 'photo', 'presentation_photo'),
                    (discovery, 'render', 'render'),
                ]:
                    patch.setattr(owner, name, recorder.wrapped(owner, name, label))
                patch.setattr(ServerSideCursor, 'fetchmany', fetch)
                with recorder.span('request'):
                    signature = read(path)
            after = snapshot()
            assert signature == expected and not recorder.stack
            assert recorder.context_rows == [24] and recorder.commercial_rows == 2000
            for label in ['request', 'state_page', 'commercial', 'publication_context', 'context_hydration',
                          'presentation_init', 'render']:
                assert recorder.stats[label]['calls'] == 1
            for label in ['page_guard', 'presentation_describe', 'presentation_photo']:
                assert recorder.stats[label]['calls'] == 24
            for metric in ['wall', 'cpu']:
                assert abs(sum(r[metric + '_exclusive'] for r in recorder.stats.values())
                           - recorder.stats['request'][metric + '_inclusive']) < 1e-6
            observations.append({'phases': dict(recorder.stats), 'sql_parents': dict(recorder.sql_parents),
                                 'fetch_parents': dict(recorder.fetch_parents),
                                 'commercial_stream_rows': recorder.commercial_rows, 'context_rows': recorder.context_rows,
                                 'backend_cpu': (after['runtime_ns'] - before['runtime_ns']) / 1e9,
                                 'backend_before': before, 'backend_after': after})
        posterior = measured_read()
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            assert cursor.fetchone()[0] == sql_pid
        median_wall = statistics.median(v['wall'] for v in controls)
        observed_wall = statistics.median(v['phases']['request']['wall_inclusive'] for v in observations)
        phases = {label: {metric: statistics.median(v['phases'][label][metric] for v in observations)
                          for metric in ['wall_inclusive', 'cpu_inclusive', 'wall_exclusive', 'cpu_exclusive']}
                  for label in observations[0]['phases']}
        routes.append({'route': route, 'controls': controls, 'posterior_control': posterior,
                       'observations': observations, 'median_phases': phases,
                       'observed_to_control_wall_ratio': observed_wall / median_wall,
                       'posterior_to_control_wall_ratio': posterior['wall'] / median_wall,
                       'backend_identity': identity})
    assert policy == (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    assert not PublicationDirty.objects.exists()
    data = {'run_id': run_id, 'result': 'CURRENT_PHASE_ATTRIBUTION_NOT_SPEEDUP',
            'profiles': 10000, 'rights': 2000, 'http_reads': 20,
            'preparation_seconds': preparation_seconds, 'routes': routes,
            'product_changed': False, 'gc_policy_preserved': True,
            'limits': ['Sequential Client HTTP, no TCP/throughput/capacity acceptance or candidate',
                       '14 unobserved reads include warm and posterior; six separate observed reads',
                       'Exclusive spans partition each observed request; median phases need not sum to median root',
                       'Observed instrumentation overhead not causally separated from host/time variation',
                       'Driver execute and named-cursor FETCH are client observations, not backend CPU',
                       'Actual owned backend CPU schedstat sampled outside request clocks; shared host',
                       'No profiler, SQL wrapper, source replacement or forced GC inside controls',
                       'Synthetic cohort shares geography/agency/photos; no real people/providers',
                       'Historical ROI rejections and fixed thresholds unchanged; no adoption from attribution']}
    output = folder / 'beta-current-request-phases.json'
    output.write_text(json.dumps(data, indent=2) + '\n')
    record_property('current_phase_http_reads', 20)
    record_property('current_phase_artifact_sha256', hashlib.sha256(output.read_bytes()).hexdigest())
