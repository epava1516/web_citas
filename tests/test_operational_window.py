"""Observed-only event aggregation, actual writer compatibility and privacy failures."""
import io
import json
import logging
import os
import time

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core import operational_events as events
from apps.core.operational_event_handler import NonBlockingOperationalHandler
from apps.core.operational_window import (
    MAX_BYTES,
    MAX_LINE_BYTES,
    MAX_LINES,
    NOTICE_TASK,
    WindowUnavailable,
    summarize_window,
)


def event(kind, timestamp=100, **values):
    return {'schema_version': 1, 'event': kind, 'timestamp_seconds': timestamp, **values}


def report(rows, start=100, end=200):
    return summarize_window(io.BytesIO(b''.join(json.dumps(row).encode() + b'\n' for row in rows)), start, end)


def test_window_boundaries_fallback_task_delivery_and_nonadditive_gap_markers():
    rows = [event('publication_read', route='state', reason='trusted_state', status_class='2xx'),
            event('publication_read', timestamp=199, route='fallback', reason='invalid_search', status_class='5xx'),
            event('publication_read', timestamp=200, route='state', reason='trusted_state', status_class='2xx'),
            event('task_result', task=NOTICE_TASK, outcome='succeeded',
                  delivery_counts={'processed': 1, 'simulated': 0, 'retry': 1, 'failed': None}, processor_disabled=False),
            event('task_result', task='other', outcome='failed')]
    rows += [event('transport_gap', dropped_events=3, write_errors=0,
                   counter_scope='process_local_cumulative')] * 2
    result = report(rows)
    assert result['coverage'] == 'unverified' and result['health'] == 'unknown'
    assert result['counts']['publication_observed'] == 2
    assert result['counts']['outside_window'] == 1
    assert result['counts']['http_5xx_observed'] == 1
    assert result['fallback_fraction_observed'] == .5
    assert result['task_outcomes_observed'] == {NOTICE_TASK: {'succeeded': 1}, 'other': {'failed': 1}}
    assert result['delivery_known_totals_observed']['retry'] == 1
    assert result['delivery_unknown_samples']['failed'] == 1
    assert result['counts']['transport_gap_markers_observed'] == 2
    assert 'dropped_events' not in json.dumps(result)


def test_empty_unknown_route_and_private_or_malformed_rows_never_imply_health():
    assert report([])['fallback_fraction_observed'] is None
    unknown = event('publication_read', route='other', reason='other', status_class='other')
    assert report([unknown])['fallback_fraction_observed'] is None
    private = event('publication_read', route='state', reason='trusted_state', status_class='2xx',
                    contact='SYNTHETIC_PRIVATE@example.invalid')
    invalid = [private, event('task_result', task=['SYNTHETIC_PRIVATE'], outcome='failed'),
               event('task_result', task='SYNTHETIC_PRIVATE', outcome='failed'),
               event('publication_read', timestamp=True, route='state', reason='trusted_state', status_class='2xx')]
    result = report(invalid)
    assert result['counts']['malformed_or_unrecognized'] == 4
    assert result['counts']['publication_observed'] == 0 and result['health'] == 'unknown'
    assert 'SYNTHETIC_PRIVATE' not in json.dumps(result)
    raw = b'{"schema_version":1,"schema_version":1}\n\xff\n{"event":NaN}\n'
    assert summarize_window(io.BytesIO(raw), 100, 200)['counts']['malformed_or_unrecognized'] == 3


@pytest.mark.parametrize('start,end', [(True, 200), (100, 100), (200, 100), (0, 3601)])
def test_invalid_window_is_fixed_error(start, end):
    with pytest.raises(WindowUnavailable, match='integer bounds'):
        report([], start, end)


def test_total_byte_and_line_limits_are_enforced_without_partial_result():
    for raw in (b'\n' * (MAX_LINES + 1),
                (b' ' * (MAX_LINE_BYTES - 1) + b'\n') * (MAX_BYTES // MAX_LINE_BYTES + 1)):
        with pytest.raises(WindowUnavailable, match='bounded limits'):
            summarize_window(io.BytesIO(raw), 100, 200)


def test_actual_nonblocking_writer_events_are_consumable_and_logger_restored(tmp_path):
    before = events.logger.handlers[:], events.logger.level, events.logger.propagate
    path = tmp_path / 'events.jsonl'
    handler = None
    with path.open('wb') as sink:
        try:
            handler = NonBlockingOperationalHandler(stream_fd=sink.fileno())
            handler.setFormatter(logging.Formatter('%(message)s'))
            events.logger.handlers = [handler]
            events.logger.setLevel(logging.INFO)
            events.logger.propagate = False
            start = int(time.time())
            events.publication_read({'route': 'fallback', 'reason': 'invalid_search'}, 200)
            events.task_result(NOTICE_TASK, 'succeeded',
                               {'processed': 1, 'simulated': 0, 'retry': 1, 'failed': 0, 'disabled': False})
            deadline = time.monotonic() + 5
            while True:
                state = handler.transport_status()
                if state['written'] == 2 and state['inflight'] == state['queued'] == 0:
                    break
                assert time.monotonic() < deadline
                time.sleep(.01)
            with path.open('rb') as source:
                result = summarize_window(source, start, int(time.time()) + 1)
            assert result['fallback_fraction_observed'] == 1
            assert result['delivery_known_totals_observed']['retry'] == 1
            assert result['counts']['malformed_or_unrecognized'] == 0
        finally:
            if handler is not None:
                handler.close()
                if handler._thread:
                    handler._thread.join(timeout=2)
                    assert not handler._thread.is_alive()
            events.logger.handlers, level, events.logger.propagate = before
            events.logger.setLevel(level)


def test_command_bounds_regular_file_and_sanitized_errors_without_partial_json(tmp_path):
    path = tmp_path / 'SYNTHETIC_PRIVATE.jsonl'
    path.write_text(json.dumps(event('task_result', task='other', outcome='failed')) + '\n')
    output = io.StringIO()
    call_command('operational_events_report', input=str(path), start=100, end=200, stdout=output)
    assert json.loads(output.getvalue())['task_outcomes_observed']['other']['failed'] == 1
    path.write_bytes(b'x' * (MAX_LINE_BYTES + 1))
    for candidate in (path, tmp_path / 'SYNTHETIC_PRIVATE_MISSING'):
        output = io.StringIO()
        with pytest.raises(CommandError) as failure:
            call_command('operational_events_report', input=str(candidate), start=100, end=200, stdout=output)
        assert output.getvalue() == ''
        assert 'SYNTHETIC_PRIVATE' not in str(failure.value)
    output = io.StringIO()
    with pytest.raises(CommandError, match='regular file'):
        call_command('operational_events_report', input='/dev/null', start=100, end=200, stdout=output)
    assert output.getvalue() == ''
    fifo = tmp_path / 'owned.fifo'
    os.mkfifo(fifo)
    with pytest.raises(CommandError, match='regular file'):
        call_command('operational_events_report', input=str(fifo), start=100, end=200, stdout=output)
