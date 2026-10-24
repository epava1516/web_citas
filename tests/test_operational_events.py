"""Fixed event vocabulary and actual owned-worker hooks; no external delivery."""
import io
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.db import connection
from django.http import HttpResponse
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core import operational_events as events
from config.celery import RecoveryAwareTask, app


@pytest.fixture
def recorded_events():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    before = events.logger.handlers[:], events.logger.level, events.logger.propagate
    events.logger.handlers = [handler]
    events.logger.setLevel(logging.INFO)
    events.logger.propagate = False
    try:
        yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    finally:
        events.logger.handlers, level, events.logger.propagate = before
        events.logger.setLevel(level)


def test_publication_events_allowlist_and_non_public_request_exclusion(recorded_events):
    response = HttpResponse('unchanged', status=200)
    def view(request):
        request._publication_route = {'route': 'state', 'reason': 'trusted_state',
                                      'private_ids': ['PRIVATE_ID'], 'query': 'PRIVATE_QUERY'}
        return response
    middleware = events.PublicationEventsMiddleware(view)
    request = SimpleNamespace(path='/PRIVATE_PATH', user='PRIVATE_USER')
    assert middleware(request) is response
    event = recorded_events()[0]
    assert set(event) == {'schema_version', 'event', 'timestamp_seconds', 'route', 'reason', 'status_class'}
    assert (event['route'], event['reason'], event['status_class']) == ('state', 'trusted_state', '2xx')
    events.publication_read({'route': ['PRIVATE_ID'], 'reason': 'PRIVATE_REASON'}, 500)
    assert recorded_events()[-1]['reason'] == 'other'
    assert recorded_events()[-1]['route'] == 'other'
    middleware = events.PublicationEventsMiddleware(lambda request: response)
    assert middleware(SimpleNamespace()) is response
    assert len(recorded_events()) == 2
    assert 'PRIVATE_' not in json.dumps(recorded_events())


def test_task_events_separate_body_success_from_delivery_result(recorded_events):
    task = RecoveryAwareTask()
    task.name = 'apps.safety.tasks.deliver_safety_notices'
    result = {'processed': 1, 'simulated': 0, 'retry': 1, 'failed': 0,
              'disabled': False, 'payload': 'PRIVATE_PAYLOAD'}
    task.on_success(result, 'PRIVATE_ID', ['PRIVATE_ARG'], {'contact': 'PRIVATE_CONTACT'})
    event = recorded_events()[0]
    assert event['outcome'] == 'succeeded' and event['delivery_counts']['retry'] == 1
    assert event['processor_disabled'] is False
    events.task_result('PRIVATE_TASK', 'PRIVATE_EXCEPTION', {'private': 'PRIVATE_RESULT'})
    assert recorded_events()[-1]['task'] == recorded_events()[-1]['outcome'] == 'other'
    assert 'PRIVATE_' not in json.dumps(recorded_events())


def test_logging_failure_cannot_break_response_or_task(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('SYNTHETIC_PRIVATE_SINK')
    monkeypatch.setattr(events.logger, 'info', fail)
    events.publication_read({'route': 'fallback', 'reason': 'invalid_search'}, 200)
    events.task_result('apps.listings.tasks.refresh_publication_state', 'failed')


@pytest.mark.django_db(transaction=True)
def test_real_worker_retry_failure_then_success_is_observable(tmp_path):
    assert connection.settings_dict['NAME'].startswith('test_')
    queue = 'operational_probe_' + uuid4().hex
    log = tmp_path / 'worker.log'
    database = connection.settings_dict
    environment = {**os.environ, 'POSTGRES_DB': database['NAME'],
                   'POSTGRES_USER': database['USER'], 'POSTGRES_PASSWORD': database['PASSWORD'],
                   'DB_HOST': database['HOST'], 'DB_PORT': str(database['PORT'])}
    def observations():
        rows = []
        for line in log.read_text().splitlines():
            if line.startswith('{'):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get('event') == 'task_result':
                    rows.append(row)
        return rows
    def wait(predicate):
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            assert process.poll() is None, 'Owned worker terminated before observation'
            if predicate():
                return
            time.sleep(.1)
        raise AssertionError('Owned worker observation timed out')
    with log.open('w') as output:
        process = subprocess.Popen([sys.executable, '-m', 'scripts.probe_operational_events', '--queue', queue],
                                   env=environment, cwd=Path(__file__).resolve().parents[1],
                                   stdout=output, stderr=subprocess.STDOUT)
    try:
        wait(lambda: ' ready.' in log.read_text())
        app.send_task('operational_probe.retry_failure', args=['SYNTHETIC_PRIVATE_ARG'], queue=queue)
        wait(lambda: {r['outcome'] for r in observations()} >= {'retry', 'failed'})
        app.send_task('operational_probe.success', args=['SYNTHETIC_PRIVATE_ARG'], queue=queue)
        wait(lambda: {r['outcome'] for r in observations()} >= {'retry', 'failed', 'succeeded'})
        rows = observations()
        assert [r['outcome'] for r in rows] == ['retry', 'failed', 'succeeded']
        assert all(r['task'] == 'other' for r in rows)
        assert 'PRIVATE' not in json.dumps(rows)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        assert process.poll() is not None
        with app.connection_for_write() as broker:
            broker.default_channel.queue_delete(queue)


@pytest.mark.django_db(transaction=True)
def test_actual_http_state_and_fallback_emit_without_changing_population(request, recorded_events, monkeypatch):
    from apps.listings import publication_state

    client = request.getfixturevalue("directory")
    publication_state.refresh_all()
    original = client.get('/es/')
    assert original.status_code == 200
    expected_ids = [row.pk for row in original.context['page'].object_list]
    expected_count = original.context['page'].paginator.count
    publication_state.mark_all()
    monkeypatch.setattr(publication_state, 'DIRTY_LIMIT', 0)
    fallback = client.get('/es/')
    assert fallback.status_code == 200
    assert [row.pk for row in fallback.context['page'].object_list] == expected_ids
    assert fallback.context['page'].paginator.count == expected_count
    rows = [row for row in recorded_events() if row['event'] == 'publication_read']
    assert len(rows) == 2
    assert rows[0]['route'] == 'state'
    assert rows[1]['route'] == 'fallback' and rows[1]['reason'] == 'state_dirty_over_limit'
