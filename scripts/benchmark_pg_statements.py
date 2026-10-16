"""Opt-in server planning/execution counters on one disposable CI database."""
import hashlib
import json
import threading
import time
from pathlib import Path

import psycopg

from scripts.benchmark_owned_cpu_observer import owned_pg_pid

FIELDS = ('plans', 'calls', 'total_plan_time', 'total_exec_time', 'max_plan_time',
          'max_exec_time', 'rows', 'shared_blks_hit', 'shared_blks_read',
          'temp_blks_read', 'temp_blks_written')


class PGStatementSampler:
    def __init__(self, output, run, inspection, database):
        owned_pg_pid(run, inspection)
        if not database['NAME'].startswith('test_promotion_gate_'):
            raise ValueError('Disposable test database required')
        port = inspection['NetworkSettings']['Ports']['5432/tcp']
        if not any(x['HostIp'] == '127.0.0.1' and x['HostPort'] == str(database['PORT']) for x in port):
            raise ValueError('Exact owned loopback PostgreSQL port required')
        if database['HOST'] != '127.0.0.1':
            raise ValueError('Owned loopback only')
        self.connection = psycopg.connect(
            host=database['HOST'], port=database['PORT'], dbname=database['NAME'],
            user=database['USER'], password=database['PASSWORD'], autocommit=True, connect_timeout=5,
            options='-c default_transaction_read_only=on -c pg_stat_statements.track=none -c statement_timeout=2000',
        )
        self.output = Path(output)
        if self.output.exists():
            self.connection.close()
            raise ValueError('Fresh output required')
        self.stop = threading.Event()
        self.thread = None
        self.error = None
        self.queries = {}
        self.samples = 0
        self.closed = False

    def snapshot(self):
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT queryid::text, query, '+','.join(FIELDS)+
                           ' FROM pg_stat_statements WHERE dbid=(SELECT oid FROM pg_database '
                           'WHERE datname=current_database()) AND toplevel')
            rows = cursor.fetchall()
            if len(rows) > 5000:
                raise ValueError('Statement bound exceeded')
            counters = {}
            for identity, query, *values in rows:
                if identity not in self.queries:
                    if len(self.queries) >= 5000:
                        raise ValueError("Cumulative statement bound exceeded")
                    self.queries[identity] = {
                        'sha256': hashlib.sha256(query.encode()).hexdigest(),
                        'sql': query[:65536], 'truncated': len(query) > 65536,
                    }
                counters[identity] = dict(zip(FIELDS, values, strict=True))
            cursor.execute('SELECT dealloc, stats_reset FROM pg_stat_statements_info')
            dealloc, reset = cursor.fetchone()
        return {'monotonic': time.monotonic(), 'counters': counters,
                'dealloc': dealloc, 'stats_reset': reset.isoformat()}

    def start(self):
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT pg_stat_statements_reset(0, '
                           '(SELECT oid FROM pg_database WHERE datname=current_database()), 0)')
        self.initial = self.snapshot()
        self.thread = threading.Thread(target=self.collect, daemon=True, name='owned-pg-statements')
        self.thread.start()

    def collect(self):
        try:
            with self.output.open('x') as stream:
                stream.write(json.dumps(self.initial)+'\n')
                for _ in range(140):
                    if self.stop.wait(1):
                        break
                    stream.write(json.dumps(self.snapshot())+'\n')
                    stream.flush()
                    self.samples += 1
                else:
                    raise RuntimeError('Bounded observation exceeded')
                stream.write(json.dumps(self.snapshot())+'\n')
        except Exception as error:
            self.error = type(error).__name__

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.thread:
            self.stop.set()
            self.thread.join(10)
            if self.thread.is_alive():
                raise RuntimeError('Statement sampler did not stop')
        self.connection.close()
        self.output.with_suffix('.queries.json').write_text(json.dumps(self.queries, indent=2)+'\n')
        self.output.with_suffix('.summary.json').write_text(json.dumps({
            'samples': self.samples, 'error': self.error,
            'scope': 'Owned database only. Server elapsed planning/execution counters, not CPU. '
                     'All application/background backends aggregated; not request attribution. '
                     'Shared extension tracking and polling overhead unquantified. Raw synthetic '
                     'normalized SQL stays in ignored artifacts. No clean p95 acceptance.',
        }, indent=2)+'\n')
