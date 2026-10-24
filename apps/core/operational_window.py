"""Bounded aggregate reports over observed events; never certify full coverage."""
import json
import os
import stat

from .operational_events import OUTCOMES, REASONS, ROUTES, TASK_NAMES

MAX_BYTES = 8 * 1024 * 1024
MAX_LINE_BYTES = 2048
MAX_LINES = 100000
NOTICE_TASK = 'apps.safety.tasks.deliver_safety_notices'
DELIVERY_KEYS = frozenset(('processed', 'simulated', 'retry', 'failed'))


class WindowUnavailable(Exception):
    """Fixed diagnostics only: no source paths, lines, exception text or subjects."""


def load_window(path, start, end):
    """Read an owned regular file without waiting for FIFO writers or echoing paths."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as source:
            metadata = os.fstat(source.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_BYTES:
                raise WindowUnavailable('Operational event input requires a bounded regular file')
            return summarize_window(source, start, end)
    except (OSError, ValueError):
        raise WindowUnavailable('Operational event input unavailable') from None


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Nonfinite JSON constant')


def _integer(value, maximum=(1 << 63) - 1):
    return type(value) is int and 0 <= value <= maximum


def _valid(row):
    if type(row) is not dict or row.get('schema_version') != 1 or type(row.get('schema_version')) is not int:
        return False
    if not _integer(row.get('timestamp_seconds')):
        return False
    base = {'schema_version', 'timestamp_seconds', 'event'}
    event = row.get('event')
    if event == 'publication_read':
        return (set(row) == base | {'route', 'reason', 'status_class'}
                and type(row['route']) is str and row['route'] in ROUTES | {'other'}
                and type(row['reason']) is str and row['reason'] in REASONS | {'other'}
                and type(row['status_class']) is str
                and row['status_class'] in {'1xx', '2xx', '3xx', '4xx', '5xx', 'other'})
    if event == 'transport_gap':
        return (set(row) == base | {'dropped_events', 'write_errors', 'counter_scope'}
                and _integer(row['dropped_events']) and _integer(row['write_errors'])
                and row['counter_scope'] == 'process_local_cumulative')
    if event != 'task_result':
        return False
    fields = base | {'task', 'outcome'}
    if type(row.get('task')) is not str or row['task'] not in TASK_NAMES | {'other'}:
        return False
    if type(row.get('outcome')) is not str or row['outcome'] not in OUTCOMES | {'other'}:
        return False
    if set(row) == fields:
        return True
    if row['task'] != NOTICE_TASK or set(row) != fields | {'delivery_counts', 'processor_disabled'}:
        return False
    counts = row['delivery_counts']
    return (type(counts) is dict and set(counts) == DELIVERY_KEYS
            and all(value is None or _integer(value, 100) for value in counts.values())
            and (row['processor_disabled'] is None or type(row['processor_disabled']) is bool))


def summarize_window(source, start, end):
    """Read binary JSONL with hard limits; half-open epoch-second window <=1h."""
    if not _integer(start) or not _integer(end) or not 0 < end - start <= 3600:
        raise WindowUnavailable('Operational window requires integer bounds spanning 1 to 3600 seconds')
    counts = {'lines': 0, 'malformed_or_unrecognized': 0, 'outside_window': 0,
              'publication_observed': 0, 'fallback_observed': 0, 'http_5xx_observed': 0,
              'publication_unclassified_observed': 0,
              'transport_gap_markers_observed': 0}
    reasons, tasks = {}, {}
    totals = {key: 0 for key in sorted(DELIVERY_KEYS)}
    unknown = {key: 0 for key in sorted(DELIVERY_KEYS)}
    disabled = {'true': 0, 'false': 0, 'unknown': 0}
    delivery_samples = 0
    total_bytes = 0
    while True:
        line = source.readline(MAX_LINE_BYTES + 1)
        if not line:
            break
        total_bytes += len(line)
        counts['lines'] += 1
        if len(line) > MAX_LINE_BYTES or total_bytes > MAX_BYTES or counts['lines'] > MAX_LINES:
            raise WindowUnavailable('Operational event input exceeds its bounded limits')
        try:
            row = json.loads(line.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
            valid = _valid(row)
        except (ValueError, RecursionError):
            valid = False
        if not valid:
            counts['malformed_or_unrecognized'] += 1
            continue
        if not start <= row['timestamp_seconds'] < end:
            counts['outside_window'] += 1
            continue
        if row['event'] == 'publication_read':
            counts['publication_observed'] += 1
            counts['fallback_observed'] += row['route'] == 'fallback'
            counts['publication_unclassified_observed'] += row['route'] == 'other'
            counts['http_5xx_observed'] += row['status_class'] == '5xx'
            reasons[row['reason']] = reasons.get(row['reason'], 0) + 1
        elif row['event'] == 'transport_gap':
            # No process identity in schema1: cumulative counters cannot be summed.
            counts['transport_gap_markers_observed'] += 1
        else:
            outcomes = tasks.setdefault(row['task'], {})
            outcomes[row['outcome']] = outcomes.get(row['outcome'], 0) + 1
            if 'delivery_counts' in row:
                delivery_samples += 1
                for key, value in row['delivery_counts'].items():
                    if value is None:
                        unknown[key] += 1
                    else:
                        totals[key] += value
                value = row['processor_disabled']
                disabled['unknown' if value is None else str(value).lower()] += 1
    observed = counts['publication_observed']
    return {'schema_version': 1, 'start_inclusive': start, 'end_exclusive': end,
            'scope': 'observed_input_only', 'coverage': 'unverified',
            'health': 'unknown', 'counts': counts, 'input_bytes': total_bytes,
            'fallback_fraction_observed': (counts['fallback_observed'] / observed
                                           if observed and not counts['publication_unclassified_observed'] else None),
            'publication_reasons_observed': reasons, 'task_outcomes_observed': tasks,
            'delivery_samples_observed': delivery_samples,
            'delivery_known_totals_observed': totals, 'delivery_unknown_samples': unknown,
            'processor_disabled_samples': disabled,
            'limitations': ['No full traffic or worker coverage proof',
                           'No durable accounting or deduplication proof',
                           'Gap counters cannot be added across unidentified processes',
                           'Zero observations do not establish health']}
