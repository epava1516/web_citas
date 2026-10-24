"""Sequential policy cost controls, reusing the independent native equivalence gate."""

import hashlib
import json
import os
import time
from functools import wraps
from pathlib import Path

import pytest
import test_production_checked_combined_equivalence as reference
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery

pytestmark = pytest.mark.django_db(transaction=True)


def signature(response):
    assert response.status_code == 200
    page = response.context['page']
    ids = [str(row.pk) for row in page.object_list]
    labels = [card['sponsorship'] for card in response.context['cards']]
    assert len(ids) == len(set(ids)) == len(labels)
    assert all(value is None for value in labels)
    return {'ordered_ids_sha256': hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
            'native_count_checked_by_reference': page.paginator.count,
            'returned': len(ids), 'sponsorship': labels}


@pytest.mark.parametrize('mode', ['normal', 'production'])
def test_policy_checked_cost100(request, settings, monkeypatch, record_property, mode):
    run = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
    assert run and connection.vendor == 'postgresql' and not settings.PRODUCTION
    client = request.getfixturevalue('directory')
    original_get = client.get
    original_render = discovery.render
    observations, evidence = [], {}

    def measured_get(path, *args, **kwargs):
        assert path.startswith(('/es/?', '/en/?'))
        assert 'profile=woman' in path and 'language=en' in path and 'q=photography' in path
        warm = original_get(path, *args, **kwargs)
        expected_signature = signature(warm)
        controls = []
        for _ in range(5):
            start, cpu = time.perf_counter(), time.process_time()
            response = original_get(path, *args, **kwargs)
            controls.append({'wall_seconds': time.perf_counter()-start,
                             'process_cpu_seconds': time.process_time()-cpu,
                             'bytes': len(response.content)})
            assert signature(response) == expected_signature
        sql, rendering = [], []
        in_render = False

        @wraps(original_render)
        def render(*render_args, **render_kwargs):
            nonlocal in_render
            assert not in_render
            in_render = True
            start = time.perf_counter()
            try:
                return original_render(*render_args, **render_kwargs)
            finally:
                rendering.append(time.perf_counter()-start)
                in_render = False

        def observe(execute, statement, params, many, context):
            start = time.perf_counter()
            phase = 'render' if in_render else 'other'
            try:
                return execute(statement, params, many, context)
            finally:
                sql.append({'seconds': time.perf_counter()-start, 'phase': phase})

        with monkeypatch.context() as patch:
            patch.setattr(discovery, 'render', render)
            start, cpu = time.perf_counter(), time.process_time()
            with connection.execute_wrapper(observe):
                response = original_get(path, *args, **kwargs)
            instrumented = {'wall_seconds': time.perf_counter()-start,
                            'process_cpu_seconds': time.process_time()-cpu, 'bytes': len(response.content)}
        assert discovery.render is original_render
        assert signature(response) == expected_signature
        assert len(rendering) == 1 and sql and not in_render
        assert rendering[0] <= instrumented['wall_seconds']
        observations.append({'path': path, **expected_signature, 'controls': controls,
                             'instrumented': instrumented, 'render_inclusive_seconds': rendering[0],
                             'sql': sql, 'sql_calls': len(sql),
                             'sql_driver_seconds': sum(row['seconds'] for row in sql)})
        return response  # The reference checks this exact signature against native authority.

    def capture(name, value):
        assert name == 'production_checked_combined_equivalence' and not evidence
        evidence.update(value)

    with monkeypatch.context() as patch:
        patch.setattr(client, 'get', measured_get)
        reference.test_combined_checked_native_pages_and_obsolete_proof(
            request, settings, capture, mode)
    assert client.get == original_get and discovery.render is original_render
    expected_pages = 114 if mode == 'normal' else 96
    assert len(observations) == evidence['pages_checked'] == expected_pages
    assert evidence['reads_do_not_repair'] and evidence['manual_repair']
    assert evidence['synthetic_metadata_only'] and not evidence['real_provider_credited']
    for measured, native in zip(observations, evidence['observations'], strict=True):
        assert measured['native_count_checked_by_reference'] == native['count']
        measured.update({key: native[key] for key in ('phase', 'city', 'checked', 'locale', 'page')})
    result = {'result': 'POLICY_CHECKED_COST100_DIAGNOSTIC_NOT_CAPACITY',
              'mode': mode, 'population': 100, 'reference': evidence, 'observations': observations,
              'warm_requests': expected_pages, 'control_requests': expected_pages*5,
              'instrumented_requests': expected_pages, 'total_reads': expected_pages*7,
              'native_parity_every_control': True, 'dirty_generations_unchanged': True,
              'capacity_accepted': False, 'worker_execution_credited': False,
              'reference_sha256': hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
              'not_measured': ['TCP', 'PostgreSQL_CPU', 'per_service_resources', 'real_provider',
                               'query_patterns', 'ORM_objects', 'validation_rule_times', 'causal_overhead'],
              'scope': 'Sequential Django client. One warm, five controls without this SQL/render observer, '
                       'then one instrumented request. Timers cover client.get; signature/native oracle '
                       'assertions are outside timers. All seven signatures match the last response, '
                       'which is checked by the unchanged independent native reference. '
                       'SQL is driver time; render inclusive overlaps SQL. Never sum them as exclusive phases. '
                       'Five controls are descriptive, not SLO percentiles. Synthetic metadata only; no live provider.'}
    output = Path(settings.BASE_DIR)/'artifacts/local-ci'/run/f'beta-policy-checked-cost100-{mode}.json'
    output.write_text(json.dumps(result, indent=2)+'\n')
    record_property('policy_checked_cost', json.dumps(result))
