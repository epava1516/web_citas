"""Replay metrics retain ambiguity, partial capture and clock boundaries."""

import copy

import pytest

from scripts.benchmark_refresh_intervals import TASK, refresh_intervals


def events():
    return [{'event': 'publish', 'task': TASK, 'id': 'task1', 'role': 'web', 'monotonic': 10.},
            {'event': 'execution', 'task': TASK, 'id': 'task1', 'role': 'worker', 'eager': False,
             'start_monotonic': 11., 'end_monotonic': 13., 'state': 'SUCCESS',
             'dirty_before': 2, 'dirty_after': 0, 'cleared': 2, 'mark_to_clear_seconds': [4., 5.]}]


def test_dispatch_and_dirty_age_are_distinct_metrics():
    result = refresh_intervals(events())
    row, = result['matched']
    assert row['publish_to_start_seconds'] == 1 and row['execution_wall_seconds'] == 2
    assert row['mark_to_clear_upper_bound_seconds'] == [4., 5.]
    assert not result['ambiguous_ids'] and not result['unmatched_publications']


@pytest.mark.parametrize('kind', ['duplicate_publish', 'duplicate_execution', 'only_publish', 'only_execution', 'eager'])
def test_ambiguous_or_partial_capture_never_invented(kind):
    rows = events()
    if kind.startswith('duplicate'):
        rows.append(copy.deepcopy(rows[0 if kind.endswith('publish') else 1]))
    elif kind == 'only_publish':
        rows = rows[:1]
    elif kind == 'only_execution':
        rows = rows[1:]
    else:
        rows[1]['eager'] = True
    result = refresh_intervals(rows)
    assert not result['matched']
    assert any(result[k] for k in ('ambiguous_ids', 'unmatched_publications', 'unmatched_executions'))


@pytest.mark.parametrize('defect', ['reversed', 'nan', 'bool', 'negative_count', 'missing_age', 'negative_age'])
def test_invalid_measurements_rejected(defect):
    rows = events()
    if defect == 'reversed':
        rows[1]['start_monotonic'] = 9.
    elif defect == 'nan':
        rows[0]['monotonic'] = float('nan')
    elif defect == 'bool':
        rows[1]['end_monotonic'] = True
    elif defect == 'negative_count':
        rows[1]['dirty_before'] = -1
    elif defect == 'missing_age':
        rows[1]['mark_to_clear_seconds'] = [4.]
    else:
        rows[1]['mark_to_clear_seconds'] = [-1., 5.]
    with pytest.raises(ValueError):
        refresh_intervals(rows)


def test_snapshot_error_preserved_without_dirty_age_claim():
    rows = events()
    rows[1]['snapshot_error'] = 'DatabaseError'
    row, = refresh_intervals(rows)['matched']
    assert row['snapshot_error'] == 'DatabaseError'
    assert 'mark_to_clear_upper_bound_seconds' not in row
