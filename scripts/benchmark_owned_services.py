"""Opt-in owned process CPU/RSS and container cgroup counters, without app hooks."""

import json
import os
import re
import threading
import time
from pathlib import Path

from scripts.benchmark_owned_backend_cpu import process_cpu
from scripts.benchmark_owned_cpu_observer import group_path, read_group


def process_row(pid):
    row = process_cpu(pid)
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    if int(fields[19]) != row['start_ticks']:
        raise ValueError('Process identity changed during read')
    return row | {'ppid': int(fields[1]), 'rss_bytes': int(fields[21]) * os.sysconf('SC_PAGE_SIZE')}


def descendant(pid, ancestor):
    for _ in range(32):
        if pid == ancestor:
            return True
        if pid <= 1:
            return False
        pid = process_row(pid)['ppid']
    raise ValueError('Process ancestry exceeded bound')


def owned_tree(identity):
    """Read only this known root's descendants; never enumerate global /proc."""
    result, pending = [], [(identity['pid'], None)]
    while pending:
        if len(result) >= 128:
            raise ValueError('Owned process tree exceeded bound')
        pid, parent = pending.pop()
        try:
            row = process_row(pid)
            if parent is None and row['start_ticks'] != identity['start_ticks']:
                raise ValueError('Owned root PID reused')
            if parent is not None and row['ppid'] != parent:
                raise ValueError('Owned child parent changed')
            children = Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        except FileNotFoundError:
            if parent is None:
                raise
            continue  # A departed child is unobserved, never counted as zero CPU.
        result.append(row)
        pending.extend((int(child), pid) for child in children)
    return result


def limit_chain(path):
    base = Path('/sys/fs/cgroup')
    if not path.is_relative_to(base):
        raise ValueError('Unexpected cgroup path')
    result = []
    while True:
        values = {}
        for name in ('cpu.max', 'memory.max', 'cpuset.cpus.effective'):
            try:
                values[name] = (path / name).read_text().strip()
            except FileNotFoundError:
                values[name] = 'not_exposed'
        result.append(values)
        if path == base:
            return result
        path = path.parent


def verify_container(run, inspection, role):
    prefix = {'postgres': 'pg', 'redis': 'redis'}[role]
    name = f"web-modelos-ci-{prefix}-{run['id']}"
    if (name not in run['containers'] or inspection['Name'] != '/' + name
            or inspection['Config']['Labels'].get('web-modelos-local-ci-run') != run['id']
            or not inspection['State']['Running']):
        raise ValueError('Owned service container mismatch')
    row = process_row(inspection['State']['Pid'])
    group = group_path(row['pid'])
    if inspection['Id'] not in str(group):
        raise ValueError('Container cgroup mismatch')
    return row, group


class OwnedServiceSampler:
    def __init__(self, output, run, roots, inspections):
        if not re.fullmatch(r'\d{8}-\d{6}-[0-9a-f]{8}', run['id']):
            raise ValueError('Exact owned run required')
        root = Path(__file__).resolve().parents[1]
        self.output = Path(output)
        if self.output != root / 'artifacts/local-ci' / run['id'] / 'service-resources.jsonl':
            raise ValueError('Exact owned resource output required')
        if self.output.exists() or set(roots) != {'web', 'worker', 'beat'}:
            raise ValueError('Fresh output and explicit three service roots required')
        for identity in (run, run['child']):
            if process_row(identity['pid'])['start_ticks'] != identity['start_ticks']:
                raise ValueError('Runner process identity changed')
        if not descendant(os.getpid(), run['child']['pid']):
            raise ValueError('Sampler is not owned by pytest launcher')
        self.roots = {}
        for role, pid in roots.items():
            row = process_row(pid)
            if row['ppid'] != os.getpid():
                raise ValueError('Service root is not a direct owned child')
            self.roots[role] = row
        if set(inspections) != {'postgres', 'redis'}:
            raise ValueError('Both exact service containers required')
        self.containers = {role: verify_container(run, inspection, role)
                           for role, inspection in inspections.items()}
        self.stop = threading.Event()
        self.phase = 'before_arrivals'
        self.summary = {
            'samples': 0, 'error_type': None, 'ticks_per_second': os.sysconf('SC_CLK_TCK'),
            'limits': {'controller': limit_chain(group_path(os.getpid())),
                       **{role: limit_chain(group) for role, (_, group) in self.containers.items()}},
            'scope': 'Known owned process trees only; per-PID CPU/RSS, RSS shared pages double count; '
                     'departed children may be unobserved, no exact CPU total or peak from samples. '
                     'Owned PG/Redis leaf cgroup CPU and memory include whole service and collector side effects. '
                     'Ancestor metadata is limits only, never attributed usage. No argv/env/SQL/rows, '
                     'no worker hooks; causal sampling overhead unmeasured, no per-request CPU attribution.',
        }

    def snapshot(self):
        containers = {}
        for role, (identity, group) in self.containers.items():
            if (process_row(identity['pid'])['start_ticks'] != identity['start_ticks']
                    or group_path(identity['pid']) != group):
                raise ValueError('Owned container identity changed')
            values = read_group(group)
            for name in ('memory.current', 'memory.peak', 'memory.max'):
                try:
                    values[name] = (group / name).read_text().strip()
                except FileNotFoundError:
                    values[name] = 'not_exposed'
            containers[role] = values
        return {'monotonic': time.monotonic(), 'phase': self.phase,
                'processes': {role: owned_tree(row) for role, row in self.roots.items()},
                'containers': containers}

    def start(self):
        initial = self.snapshot()  # Ownership/read failures stop before starting arrivals.
        self.stream = self.output.open('x')
        self.write(initial)
        self.thread = threading.Thread(target=self.run, daemon=True, name='owned-service-resources')
        self.thread.start()

    def write(self, row):
        self.stream.write(json.dumps(row) + '\n')
        self.stream.flush()
        self.summary['samples'] += 1

    def run(self):
        started = time.thread_time()
        try:
            for _ in range(1200):
                if self.stop.wait(1):
                    break
                self.write(self.snapshot())
            else:
                raise RuntimeError('Bounded service sampling exceeded')
        except Exception as error:
            self.summary['error_type'] = type(error).__name__
        finally:
            self.summary['collector_thread_cpu_seconds'] = time.thread_time() - started

    def close(self):
        self.stop.set()
        self.thread.join(5)
        if self.thread.is_alive():
            raise RuntimeError('Service sampler did not stop')
        try:
            self.write(self.snapshot())
        except Exception as error:
            self.summary['error_type'] = type(error).__name__
        finally:
            self.stream.close()
        self.output.with_suffix('.summary.json').write_text(json.dumps(self.summary, indent=2) + '\n')
        return self.summary
