"""Explicit sequential attribution of the current stored-state page guard."""

import gc
import time

import pytest
from django.core.management import call_command
from django.db import connection, models
from django.db.models import query as query_module
from django.forms import models as form_models
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, public_validation, publication_state
from apps.listings.forms import ContactsForm
from apps.listings.models import Revision
from apps.listings.public_validation import PublicationContext, SnapshotDetails
from scripts.benchmark_rule_profile import RuleProfile
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_current_page_rule_attribution(request, monkeypatch, record_property):
    if not any(str(arg).split('::')[0] == 'tests/test_directory_current_rule_profile.py'
               for arg in request.config.args):
        pytest.skip('Explicit owned sequential rule diagnostic only')
    assert connection.vendor == 'postgresql'
    client = request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state')
    results = []
    for params in ({}, {'q': 'photography'}, {'q': 'synthetic'}):
        control = client.get('/es/', params)
        assert control.status_code == 200
        assert control.wsgi_request._publication_route['route'] == 'state'
        expected_ids = [row.pk for row in control.context['page'].object_list]
        expected_count = control.context['page'].paginator.count
        assert len(expected_ids) == 24
        profile = RuleProfile(cpu_clock=time.thread_time)
        targets = [
            (PublicationContext, '__init__'),
            (PublicationContext, '_bound_validation'),
            (publication_state, 'publicly_visible'),
            (publication_state, 'all_state_current'),
            (discovery, 'render'),
            (form_models, 'construct_instance'),
            (SnapshotDetails, '_post_clean'),
            (ContactsForm, '_post_clean'),
            (Revision, 'full_clean'),
            (models.Model, '__init__'),
            (models.QuerySet, '_fetch_all'),
            (query_module, 'prefetch_related_objects'),
            (public_validation, 'read_publication_values'),
        ]
        collections, gc_started = [], {}

        def observe_gc(phase, info):
            generation = info['generation']
            if phase == 'start':
                gc_started[generation] = (time.perf_counter(), time.thread_time(),
                                          [frame['rule'] for frame in profile.stack.get()])
            elif generation in gc_started:
                wall_start, cpu_start, parents = gc_started.pop(generation)
                collections.append({'generation': generation,
                                    'wall_seconds': time.perf_counter() - wall_start,
                                    'thread_cpu_seconds': time.thread_time() - cpu_start,
                                    'parents': parents})

        with monkeypatch.context() as patches:
            for owner, name in targets:
                patches.setattr(owner, name, profile.wrap(owner.__name__ + '.' + name,
                                                         getattr(owner, name)))

            def sql_event(execute, sql, values, many, context):
                return profile.wrap('sql.cursor_execute', execute)(sql, values, many, context)

            started, cpu = time.perf_counter(), time.thread_time()
            gc.callbacks.append(observe_gc)
            try:
                with connection.execute_wrapper(sql_event):
                    response = client.get('/es/', params)
            finally:
                gc.callbacks.remove(observe_gc)
            wall, cpu = time.perf_counter() - started, time.thread_time() - cpu
        assert response.status_code == 200
        assert response.wsgi_request._publication_route['route'] == 'state'
        assert response['Cache-Control'] == 'no-store'
        assert response.context['page'].paginator.count == expected_count
        assert [row.pk for row in response.context['page'].object_list] == expected_ids
        rows = profile.report()
        by_rule = {row['rule']: row for row in rows}
        assert by_rule['PublicationContext._bound_validation']['calls'] == 48
        assert by_rule['Revision.full_clean']['calls'] == 48
        results.append({'params': params, 'count': expected_count, 'page_size': 24,
                        'wall_seconds': wall, 'thread_cpu_seconds': cpu, 'rules': rows,
                        'gc_collections': collections})
    record_property('current_page_rule_attribution', results)
    record_property('scope', 'One control then instrumented sequential request per case; '
                    'current stored-state route and native 24-row guard, PostgreSQL synthetic10k. '
                    'No arguments, SQL text, parameters or response bodies recorded. '
                    'Model construction/fetch/prefetch wrappers and GC start-stop callbacks add overhead. '
                    'GC intervals overlap rule events; do not sum them. No GC policy changes. '
                    'Nested exclusive times discount observed direct children only. '
                    'No concurrent load, operational p95, DB CPU/waits or causal overhead measurement.')


def test_owned_detail_rule_attribution(request, monkeypatch, record_property):
    from django.core import signing
    from django.forms.models import BaseModelForm

    from apps.listings import moderation, moderation_views, submissions
    from apps.listings.forms import DetailsForm

    if not any(str(arg).split('::')[0] == 'tests/test_directory_current_rule_profile.py'
               for arg in request.config.args):
        pytest.skip('Explicit owned sequential rule diagnostic only')
    assert connection.vendor == 'postgresql'
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
    call_command('refresh_publication_state')
    results = []
    for language in ('es', 'en'):
        path = f"/{language}/listing/{dataset['sample_ids'][0]}/"
        control = client.get(path)
        assert control.status_code == 200
        profile = RuleProfile(cpu_clock=time.thread_time)
        targets = [
            (moderation_views, 'publicly_visible'),
            (moderation, 'validate_submission'),
            (submissions, 'publication_ready'),
            (DetailsForm, '__init__'),
            (BaseModelForm, '_post_clean'),
            (Revision, 'full_clean'),
            (moderation_views, 'render'),
            (models.QuerySet, '_fetch_all'),
            (models.Model, '__init__'),
        ]
        sql_groups = {}
        with monkeypatch.context() as patches:
            for owner, name in targets:
                patches.setattr(owner, name, profile.wrap(owner.__name__ + '.' + name,
                                                         getattr(owner, name)))

            def sql_event(execute, sql, values, many, context):
                stage = ('guard' if any(frame['rule'].endswith('.publicly_visible')
                                       for frame in profile.stack.get()) else 'other')
                started, cpu = time.perf_counter(), time.thread_time()
                try:
                    return execute(sql, values, many, context)
                finally:
                    row = sql_groups.setdefault(stage, {'calls': 0, 'wall_seconds': 0,
                                                       'thread_cpu_seconds': 0})
                    row['calls'] += 1
                    row['wall_seconds'] += time.perf_counter() - started
                    row['thread_cpu_seconds'] += time.thread_time() - cpu

            started, cpu = time.perf_counter(), time.thread_time()
            with connection.execute_wrapper(sql_event):
                response = client.get(path)
            wall, cpu = time.perf_counter() - started, time.thread_time() - cpu
        assert response.status_code == 200
        assert response['Cache-Control'] == 'no-store'
        assert response.context['public'] == control.context['public']
        salt = 'public-report-target-v1'
        assert signing.loads(response.context['report_target'], salt=salt) == signing.loads(
            control.context['report_target'], salt=salt)
        assert [x.pk for x in response.context['photos']] == [x.pk for x in control.context['photos']]
        rows = profile.report()
        assert next(x for x in rows if x['rule'] == 'Revision.full_clean')['calls'] == 2
        results.append({'language': language, 'wall_seconds': wall, 'thread_cpu_seconds': cpu,
                        'sql_groups': sql_groups, 'rules': rows})
    record_property('current_detail_rule_attribution', results)
    record_property('scope', 'Two sequential synthetic detail cases, control then instrumented; '
                    'native guard unchanged. SQL grouped by enclosing guard without storing SQL, '
                    'values or bodies. Query intervals overlap rule totals, not DB CPU. '
                    'No concurrent load, operational p95, GC attribution or causal overhead.')
