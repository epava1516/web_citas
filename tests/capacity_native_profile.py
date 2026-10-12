"""Bounded diagnostics on the owned synthetic capacity database, never production."""

import json
import os
import re
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread

import psycopg
from django.db import connection


@contextmanager
def capture(stage):
    config = connection.settings_dict
    if config['HOST'] != 'pg' or config['NAME'] != 'test_capacity_ci':
        raise RuntimeError('Native diagnostic requires the owned capacity test database')
    live_backend, backend_history = [None], []
    stem = f'/tmp/capacity-native-{stage}-{os.getpid()}-{time.monotonic_ns()}'
    events, errors, stop = [], [], Event()
    # Independent observer owns only this disposable synthetic database. Business
    # queries keep their restricted runtime connection and unchanged privileges.
    observer = psycopg.connect(host='pg', port=5432, dbname=config['NAME'],
                               user='ci', password='ci-synthetic', autocommit=True,
                               connect_timeout=5, options='-c statement_timeout=1000')

    def statements():
        with observer.cursor() as cursor:
            cursor.execute('''SELECT s.userid,s.queryid,s.calls,s.total_exec_time,
                s.rows,s.shared_blk_read_time,s.shared_blk_write_time,
                s.temp_blk_read_time,s.temp_blk_write_time,s.query,s.toplevel
                FROM pg_stat_statements s
                WHERE s.dbid=(SELECT oid FROM pg_database WHERE datname=current_database())
                AND s.userid<>(SELECT oid FROM pg_roles WHERE rolname=current_user)''')
            known = ('rights_evidence_row_hash', 'rights_evidence_link',
                     'rights_evidence_source_', 'rights_evidence_events_v1',
                     'rights_evidence_locked_head', 'pg_roles', 'pg_class',
                     'pg_attribute', 'pg_trigger', 'pg_proc', 'listings_revision')
            # SQL is inspected only to emit these fixed code labels, never stored.
            return [list(row[:-2]) + [row[-1],
                    [label for label in known if label in (row[-2] or '')]]
                    for row in cursor.fetchall()]

    def bind_backend(execute, statement, params, many, context):
        # request_started can close an expired Django connection. Bind only when
        # business SQL actually executes, preserving its connection lifecycle.
        backend = context['connection'].connection.info.backend_pid
        if backend != live_backend[0]:
            live_backend[0] = backend
            backend_history.append([time.monotonic_ns(), backend])
        return execute(statement, params, many, context)

    before = statements()

    def sample():
        try:
            with observer.cursor() as cursor:
                while not stop.is_set() and len(events) < 4000:
                    cursor.execute('SELECT state,wait_event_type,wait_event '
                                   'FROM pg_stat_activity WHERE pid=%s', [live_backend[0]])
                    row = cursor.fetchone()
                    events.append([time.monotonic_ns(), *(row or (None, None, None))])
                    stop.wait(.025)
        except Exception as error:
            errors.append(type(error).__name__)

    sampler = Thread(target=sample, name='capacity-pg-observer', daemon=True)
    log = Path(stem + '.log').open('w')
    profiler = subprocess.Popen([
        '/opt/diagnostic-py-spy', 'record', '--pid', str(os.getpid()),
        '--native', '--idle', '--threads', '--rate', '100', '--duration', '100',
        '--format', 'speedscope', '--output', stem + '.stacks.json',
    ], stdout=log, stderr=subprocess.STDOUT)
    sampler.start()
    maps = Path('/proc/self/maps').read_text()
    begin = time.monotonic_ns()
    try:
        with connection.execute_wrapper(bind_backend):
            yield
    finally:
        original_failure = sys.exc_info()[0] is not None
        end = time.monotonic_ns()
        stop.set()
        sampler.join(timeout=5)
        if sampler.is_alive():
            raise RuntimeError('PG observer did not stop')
        after = statements()
        observer.close()
        if profiler.poll() is None:
            profiler.send_signal(signal.SIGINT)
        try:
            profiler.wait(timeout=10)
        except subprocess.TimeoutExpired:
            profiler.kill()
            profiler.wait(timeout=5)
            errors.append('ProfilerTimeout')
        log.close()
        stacks = Path(stem + '.stacks.json')
        if not stacks.is_file() or stacks.stat().st_size == 0:
            errors.append('NativeStacksMissing')
        profiler_log = Path(stem + '.log').read_text()[-2000:]
        matched = re.search(r'Samples: (\d+) Errors: (\d+)', profiler_log)
        if not matched or int(matched[1]) == 0:
            errors.append('NativeSamplesMissing')
        if not backend_history or not any(row[1] is not None for row in events):
            errors.append('BackendNotObserved')
        Path(stem + '.pg.json').write_text(json.dumps({
            'schema': 'capacity-native-v2', 'stage': stage, 'python_pid': os.getpid(),
            'backend_pid': live_backend[0], 'backend_history': backend_history,
            'memory_maps': maps,
            'begin_ns': begin, 'end_ns': end, 'events': events,
            'statements_before': before, 'statements_after': after,
            'profiler_exit': profiler.returncode,
            'profiler_log': profiler_log, 'errors': errors,
            'sampling_errors': int(matched[2]) if matched else None,
            'sampling_status': ('partial' if int(matched[2]) else 'complete') if matched else 'invalid',
            'scope': 'Intrusive diagnostic only. 25ms sampled waits may miss short events; '
                     'ClientRead means server waiting for client. Statement differences '
                     'include other restricted-role workers in the same database interval; '
                     'nested times overlap. Python observer thread is identified by name. '
                     'No SQL text, parameters, frame locals or payloads captured.',
        }, sort_keys=True))
        if errors and not original_failure:
            raise RuntimeError('Native diagnostic invalid: ' + ','.join(errors))
