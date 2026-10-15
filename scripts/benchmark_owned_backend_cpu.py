"""Read CPU of one SQL-identified backend inside the exact owned CI container."""

import os
import subprocess
import time
from pathlib import Path

from scripts.benchmark_owned_cpu_observer import group_path, owned_pg_pid


def process_cpu(pid, proc_root=Path('/proc')):
    if type(pid) is not int or pid <= 1:
        raise ValueError('Exact positive process ID required')
    text = (proc_root / str(pid) / 'stat').read_text()
    if int(text.split(' ', 1)[0]) != pid:
        raise ValueError('Process identity mismatch')
    fields = text.rsplit(')', 1)[1].split()
    values = [int(fields[i]) for i in (11, 12, 19)]
    if min(values) < 0 or values[2] == 0:
        raise ValueError('Invalid process CPU counters')
    return {'pid': pid, 'user_ticks': values[0], 'system_ticks': values[1],
            'start_ticks': values[2], 'monotonic': time.monotonic()}


def namespace_pid(pid):
    for line in Path(f'/proc/{pid}/status').read_text().splitlines():
        if line.startswith('NSpid:'):
            return int(line.split()[-1])
    raise ValueError('PID namespace identity unavailable')


def owned_backend(run, inspection, sql_pid):
    owned_pg_pid(run, inspection)  # Validate exact run/name/label/live postmaster first.
    if type(sql_pid) is not int or sql_pid <= 1:
        raise ValueError('Exact SQL backend PID required')
    name = inspection['Name'].removeprefix('/')
    # Docker scopes enumeration to this verified container. Never enumerate /proc.
    lines = subprocess.check_output(['docker', 'top', name, '-eo', 'pid'], text=True).splitlines()
    if not lines or lines[0].strip() != 'PID' or len(lines) > 129:
        raise ValueError('Unexpected owned process inventory')
    matches = []
    for line in lines[1:]:
        pid = int(line.strip())
        group = group_path(pid)
        if inspection['Id'] not in str(group):
            raise ValueError('Process outside owned container cgroup')
        if namespace_pid(pid) == sql_pid:
            matches.append(process_cpu(pid) | {'container_id': inspection['Id'],
                                               'sql_pid': sql_pid, 'cgroup': str(group)})
    if len(matches) != 1:
        raise ValueError('Unique owned SQL backend not found')
    return matches[0]


def backend_snapshot(identity):
    pid = identity['pid']
    if (str(group_path(pid)) != identity['cgroup']
            or namespace_pid(pid) != identity['sql_pid']):
        raise ValueError('Owned backend changed')
    result = process_cpu(pid)
    if result['start_ticks'] != identity['start_ticks']:
        raise ValueError('Owned backend PID reused')
    return result


def backend_delta(before, after, ticks_per_second=None):
    hz = os.sysconf('SC_CLK_TCK') if ticks_per_second is None else ticks_per_second
    if type(hz) is not int or hz <= 0:
        raise ValueError('Valid clock tick frequency required')
    if (before['pid'], before['start_ticks']) != (after['pid'], after['start_ticks']):
        raise ValueError('Backend identity changed')
    delta = {k: after[k] - before[k] for k in ('user_ticks', 'system_ticks')}
    if min(delta.values()) < 0 or after['monotonic'] <= before['monotonic']:
        raise ValueError('Invalid backend CPU interval')
    return {'ticks_per_second': hz, 'cpu_seconds': sum(delta.values()) / hz,
            'delta': delta, 'elapsed_seconds': after['monotonic'] - before['monotonic']}


def statement_family(sql):
    """Labels only for known generated SQL; never retain SQL or parameters."""
    if '"_pv_history"' in sql:
        return 'hydration'
    if '"search_document"' in sql and '@@' in sql:
        return 'search_count' if 'COUNT(' in sql else 'search_page'
    if 'listings_publicationstate' in sql and '"eligible"' in sql:
        return 'listing_count' if 'COUNT(' in sql else 'listing_page'
    if 'listings_publicationdirty' in sql:
        return 'dirty'
    if 'listings_publicationstate' in sql:
        return 'state_current'
    if '"catalog_' in sql:
        return 'catalog'
    if '"mediafiles_' in sql:
        return 'media'
    if '"safety_' in sql:
        return 'rights'
    return 'other'
