"""Selected-page ORM attribution; no ranking candidate or capacity benchmark."""

import cProfile
import hashlib
import json
import os
import pstats
import statistics
import time
from collections import Counter
from pathlib import Path

import pytest
from beta_current_request_phases import PhaseRecorder
from django.db import connection
from django.db.models import Model
from django.db.models import query as query_module
from django.db.models.sql.compiler import SQLCompiler
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation, publication_state
from apps.listings.models import PublicationDirty
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def profile_rows(profile, root, key):
    rows = []
    for (filename, line, name), (primitive, total, own, cumulative, _) in pstats.Stats(profile).stats.items():
        path = Path(filename)
        source = str(path.relative_to(root)) if path.is_relative_to(root) else filename
        rows.append({'source': source, 'line': line, 'function': name, 'primitive_calls': primitive,
                     'total_calls': total, 'self_seconds': own, 'inclusive_seconds': cumulative})
    return sorted(rows, key=lambda row: row[key], reverse=True)[:80]


def test_selected_page_python_hydration_attribution(request, settings, monkeypatch, record_property):
    run_id = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    populate(1000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    reads = 0

    def read(path):
        nonlocal reads
        reads += 1
        response = client.get(path)
        assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
        assert response.wsgi_request._publication_route['route'] == 'state'
        page = response.context['page']
        assert page.paginator.count == 1000 and len(page.object_list) == 24
        return (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                tuple(str(row.pk) for row in page.object_list),
                tuple(c['sponsorship'] for c in response.context['cards']))

    routes = []
    for route, path in [('directory_es', '/es/'), ('search_en', '/en/?q=synthetic')]:
        expected = read(path)
        controls = []
        for _ in range(5):
            wall, cpu = time.perf_counter(), time.thread_time()
            assert read(path) == expected
            controls.append({'wall': time.perf_counter() - wall, 'app_cpu': time.thread_time() - cpu})
        observations = []
        for _ in range(3):
            recorder = PhaseRecorder()
            state = {'active': False, 'rows': [], 'models': Counter()}
            original_read = public_validation.read_publication_values
            original_prefetch = query_module.prefetch_one_level
            original_compile = SQLCompiler.as_sql
            original_model = Model.__init__

            def hydration(*args, **kwargs):
                assert not state['active']
                state['active'] = True
                try:
                    with recorder.span('hydration'):
                        rows = original_read(*args, **kwargs)
                    state['rows'].append(len(rows))
                    return rows
                finally:
                    state['active'] = False

            def prefetch(instances, prefetcher, lookup, level):
                if not state['active']:
                    return original_prefetch(instances, prefetcher, lookup, level)
                label = 'prefetch:' + lookup.prefetch_to + ':' + str(level)
                with recorder.span(label):
                    return original_prefetch(instances, prefetcher, lookup, level)

            def compile_sql(*args, **kwargs):
                if not state['active']:
                    return original_compile(*args, **kwargs)
                with recorder.span('sql_compile'):
                    return original_compile(*args, **kwargs)

            def model_init(instance, *args, **kwargs):
                if not state['active']:
                    return original_model(instance, *args, **kwargs)
                with recorder.span('model_init'):
                    result = original_model(instance, *args, **kwargs)
                    state['models'][instance._meta.label] += 1
                    return result

            def sql(execute, statement, params, many, context):
                if not state['active']:
                    return execute(statement, params, many, context)
                recorder.sql_parents[recorder.stack[-1]['name']] += 1
                with recorder.span('sql_execute'):
                    return execute(statement, params, many, context)

            with monkeypatch.context() as patch, connection.execute_wrapper(sql):
                patch.setattr(public_validation, 'read_publication_values', hydration)
                patch.setattr(query_module, 'prefetch_one_level', prefetch)
                patch.setattr(SQLCompiler, 'as_sql', compile_sql)
                patch.setattr(Model, '__init__', model_init)
                assert read(path) == expected
            assert state['rows'] == [24] and not recorder.stack
            assert recorder.stats['hydration']['calls'] == 1
            assert recorder.stats['sql_compile']['calls'] > 0 and state['models']['listings.Listing'] == 24
            for metric in ['wall', 'cpu']:
                assert abs(sum(v[metric + '_exclusive'] for v in recorder.stats.values())
                           - recorder.stats['hydration'][metric + '_inclusive']) < 1e-6
            observations.append({'phases': dict(recorder.stats), 'sql_parents': dict(recorder.sql_parents),
                                 'models': dict(state['models']), 'rows': state['rows']})
        profile = cProfile.Profile()
        original_read = public_validation.read_publication_values
        profiled_rows = []

        def profiled_hydration(*args, **kwargs):
            profile.enable()
            try:
                rows = original_read(*args, **kwargs)
            finally:
                profile.disable()
            profiled_rows.append(len(rows))
            return rows

        with monkeypatch.context() as patch:
            patch.setattr(public_validation, 'read_publication_values', profiled_hydration)
            assert read(path) == expected
        assert profiled_rows == [24]
        assert read(path) == expected
        labels = observations[0]['phases']
        medians = {label: {metric: statistics.median(v['phases'][label][metric] for v in observations)
                           for metric in ['wall_inclusive', 'cpu_inclusive', 'wall_exclusive', 'cpu_exclusive']}
                   for label in labels}
        routes.append({'route': route, 'controls': controls, 'observations': observations,
                       'median_phases': medians,
                       'hydration_profile_top_self': profile_rows(profile, settings.BASE_DIR, 'self_seconds'),
                       'hydration_profile_top_inclusive': profile_rows(profile, settings.BASE_DIR, 'inclusive_seconds')})
    assert reads == 22 and not PublicationDirty.objects.exists()
    result = {'run_id': run_id, 'result': 'HYDRATION_PYTHON_ATTRIBUTION_NOT_SPEEDUP',
              'profiles': 1000, 'rights': 0, 'http_reads': reads, 'routes': routes,
              'product_changed': False,
              'limits': ['Selected page24 only, not the10000/2000 promotional cohort or TCP',
                         'Six span observations and two separate scoped cProfile requests; controls unobserved',
                         'Compilation, nested prefetch and model construction exclusive spans partition each hydration',
                         'Driver execute is inclusive client time, not backend CPU; fetch/conversion remain in parents',
                         'cProfile self/inclusive times are instrumented wall times; inclusive times overlap',
                         'Relation names/model labels only, no SQL/params/arguments/records in summaries',
                         'No variant, no adopted speedup and no permission to revive rejected experiments']}
    output = settings.BASE_DIR / 'artifacts/local-ci' / run_id / 'beta-hydration-python.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    record_property('hydration_python_reads', reads)
    record_property('hydration_python_artifact_sha256', hashlib.sha256(output.read_bytes()).hexdigest())
