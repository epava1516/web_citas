"""Explicit sequential attribution of the current stored-state page guard."""

import time

import pytest
from django.core.management import call_command
from django.db import connection
from django.forms import models as form_models
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, publication_state
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
        ]
        with monkeypatch.context() as patches:
            for owner, name in targets:
                patches.setattr(owner, name, profile.wrap(owner.__name__ + '.' + name,
                                                         getattr(owner, name)))

            def sql_event(execute, sql, values, many, context):
                return profile.wrap('sql.cursor_execute', execute)(sql, values, many, context)

            started, cpu = time.perf_counter(), time.thread_time()
            with connection.execute_wrapper(sql_event):
                response = client.get('/es/', params)
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
                        'wall_seconds': wall, 'thread_cpu_seconds': cpu, 'rules': rows})
    record_property('current_page_rule_attribution', results)
    record_property('scope', 'One control then instrumented sequential request per case; '
                    'current stored-state route and native 24-row guard, PostgreSQL synthetic10k. '
                    'No arguments, SQL text, parameters or response bodies recorded. '
                    'Nested exclusive times discount observed direct children only. '
                    'No concurrent load, operational p95, DB CPU/waits or causal overhead measurement.')
