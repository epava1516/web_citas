"""Replay owned Celery refresh events; publish-to-start is not queue-only time."""

import math
from collections import defaultdict

TASK = 'apps.listings.tasks.refresh_publication_state'


def refresh_intervals(events):
    publications, executions = defaultdict(list), defaultdict(list)
    for event in events:
        if event.get('task') != TASK:
            continue
        task_id = event.get('id')
        if not isinstance(task_id, str) or not task_id:
            raise ValueError('Refresh task identity required')
        if event.get('event') == 'publish' and event.get('role') in {'web', 'beat'}:
            publications[task_id].append(event)
        elif (event.get('event') == 'execution' and event.get('role') == 'worker'
              and event.get('eager') is False):
            executions[task_id].append(event)
    result = {'matched': [], 'ambiguous_ids': [], 'unmatched_publications': [],
              'unmatched_executions': [], 'scope':
              'Publish signal to worker start includes publisher, broker and dispatch; '
              'not exclusive queue residence. Dirty mark-to-clear values are database-clock '
              'upper bounds at observer query, not exact clear instants. Partial capture '
              'and retries remain explicit; no claim about unobserved tasks.'}
    for task_id in sorted(set(publications) | set(executions)):
        pubs, runs = publications[task_id], executions[task_id]
        if len(pubs) > 1 or len(runs) > 1:
            result['ambiguous_ids'].append(task_id)
            continue
        if not pubs:
            result['unmatched_executions'].append(task_id)
            continue
        if not runs:
            result['unmatched_publications'].append(task_id)
            continue
        pub, run = pubs[0], runs[0]
        times = (pub['monotonic'], run['start_monotonic'], run['end_monotonic'])
        if (any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in times)
                or not times[0] <= times[1] <= times[2]):
            raise ValueError('Ordered finite refresh timestamps required')
        row = {'id': task_id, 'publisher_role': pub['role'], 'state': run.get('state'),
               'published_monotonic': times[0], 'start_monotonic': times[1],
               'end_monotonic': times[2], 'publish_to_start_seconds': times[1] - times[0],
               'execution_wall_seconds': times[2] - times[1]}
        if 'snapshot_error' in run:
            row['snapshot_error'] = run['snapshot_error']
        elif all(k in run for k in ('dirty_before', 'dirty_after', 'cleared', 'mark_to_clear_seconds')):
            counts = [run[k] for k in ('dirty_before', 'dirty_after', 'cleared')]
            ages = run['mark_to_clear_seconds']
            if (any(type(v) is not int or v < 0 for v in counts)
                    or counts[2] > counts[0] or not isinstance(ages, list) or len(ages) != counts[2]
                    or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in ages)):
                raise ValueError('Consistent dirty mark observations required')
            row.update(dirty_before=counts[0], dirty_after=counts[1], cleared=counts[2],
                       mark_to_clear_upper_bound_seconds=ages)
        result['matched'].append(row)
    return result
