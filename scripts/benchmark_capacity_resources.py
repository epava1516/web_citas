"""Host-side reader for six exact capacity containers; no global process scan.

Optional functional observer. Snapshots are observations, not capacity,
per-request attribution, exclusive workload CPU, or synchronous memory peaks.
"""

import json
import os
import re
import stat
import subprocess
import threading
import time
from pathlib import Path

from scripts.benchmark_capacity_phase import MAX_BYTES, PHASE_PATH, decode_phase
from scripts.benchmark_owned_cpu_observer import group_path, read_group
from scripts.benchmark_owned_services import process_row

ROLES = frozenset({'controller', 'app', 'pg', 'redis', 'objects', 'caddy'})
LABEL = 'web-modelos-capacity-run'


class CapacityContainerPending(ValueError):
    """An exact owned container was created but has not started yet."""


def verify_capacity_identity(run_id, role, inspection):
    """Reject foreign metadata before reading any host process or cgroup."""
    if not re.fullmatch(r'\d{8}-\d{6}-[0-9a-f]{8}', run_id) or role not in ROLES:
        raise ValueError('Exact capacity run and service role required')
    expected = '/web-modelos-capacity-' + run_id + '-' + role
    state = inspection.get('State', {})
    container_id = inspection.get('Id', '')
    if (inspection.get('Name') != expected
            or inspection.get('Config', {}).get('Labels', {}).get(LABEL) != run_id
            or not re.fullmatch(r'[0-9a-f]{64}', container_id)):
        raise ValueError('Owned capacity container mismatch')
    if (state.get('Status') == 'created' and state.get('Running') is False
            and state.get('Paused') is False and state.get('Restarting') is False
            and type(state.get('Pid')) is int and state['Pid'] == 0):
        raise CapacityContainerPending('Owned capacity container not started')
    if (state.get('Running') is not True or state.get('Paused') is not False
            or state.get('Restarting') is not False
            or type(state.get('Pid')) is not int or state['Pid'] <= 1):
        raise ValueError('Owned capacity container mismatch')
    identity = process_row(state['Pid'])
    group = group_path(identity['pid'])
    if group.name not in {container_id, 'docker-' + container_id + '.scope'}:
        raise ValueError('Capacity container cgroup mismatch')
    return identity, group


class CapacityResourceReader:
    """Explicit host-side identities; callers supply inspect results, never discovery."""

    def __init__(self, run_id, inspections):
        if set(inspections) != ROLES:
            raise ValueError('All six exact service inspections required')
        self.identities = {
            role: verify_capacity_identity(run_id, role, inspection)
            for role, inspection in inspections.items()
        }
        if len({row['pid'] for row, _ in self.identities.values()}) != len(ROLES):
            raise ValueError('Distinct container init processes required')
        self.run_id = run_id
        self.manifest = {
            role: {'run': run_id, 'container_id': inspections[role]['Id'],
                   'name': inspections[role]['Name'], 'init_pid': row['pid'],
                   'init_start_ticks': row['start_ticks'], 'cgroup': str(group)}
            for role, (row, group) in self.identities.items()
        }

    def read_phase(self):
        """Read only the verified app init root; revalidate around the bounded read."""
        identity, group = self.identities['app']

        def check():
            if (process_row(identity['pid'])['start_ticks'] != identity['start_ticks']
                    or group_path(identity['pid']) != group):
                raise ValueError('Capacity app phase identity changed')

        check()
        path = Path('/proc') / str(identity['pid']) / 'root' / PHASE_PATH.relative_to('/')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES:
                raise ValueError('Bounded regular phase signal required')
            data = stream.read(MAX_BYTES + 1)
        check()
        return decode_phase(data, self.run_id)

    def snapshot(self, phase):
        if phase not in {'before_arrivals', 'arrivals_and_drain', 'idle_after'}:
            raise ValueError('Explicit workload phase required')
        started = time.monotonic()
        services = {}
        for role, (identity, group) in self.identities.items():
            current = process_row(identity['pid'])
            if (current['start_ticks'] != identity['start_ticks']
                    or group_path(identity['pid']) != group):
                raise ValueError('Capacity service identity changed')
            counters = read_group(group)
            counters.update({name: (group / name).read_text().strip()
                             for name in ('memory.current', 'memory.peak', 'memory.max',
                                          'memory.swap.current', 'memory.swap.max', 'cpu.max')})
            # docker exec processes need not descend from container init. Read only
            # the verified leaf inventory, never a global /proc enumeration.
            pids = (group / 'cgroup.procs').read_text().split()
            if len(pids) > 256 or any(not pid.isdecimal() for pid in pids):
                raise ValueError('Bounded owned cgroup process inventory required')
            processes = []
            for pid in map(int, pids):
                try:
                    row = process_row(pid)
                    if group_path(pid) != group:
                        raise ValueError('Process outside owned capacity cgroup')
                    processes.append(row)
                except (FileNotFoundError, ProcessLookupError):
                    continue  # Departed processes are unobserved, never zero CPU.
            services[role] = {'counters': counters, 'processes': processes}
        return {'run': self.run_id, 'phase': phase, 'started_monotonic': started,
                'finished_monotonic': time.monotonic(), 'services': services}


class CapacityResourceObserver:
    """Optional host observer, outside the workload budget; diagnostic only."""

    def __init__(self, run_id, output, docker, *, preparation_seconds=600):
        if not re.fullmatch(r'\d{8}-\d{6}-[0-9a-f]{8}', run_id):
            raise ValueError('Exact capacity run required')
        root = Path(__file__).resolve().parents[1]
        self.output = Path(output)
        if self.output != root / 'artifacts/capacity-environment' / run_id:
            raise ValueError('Exact capacity output required')
        launcher = json.loads((self.output / 'launcher-started.json').read_text())
        expected = {'web-modelos-capacity-' + run_id + '-' + role for role in ROLES}
        if (launcher['id'] != run_id or launcher['pid'] != os.getpid()
                or launcher['start_ticks'] != process_row(os.getpid())['start_ticks']
                or set(launcher['owned']) != expected):
            raise ValueError('Exact live capacity launcher required')
        if preparation_seconds not in (600, 1800, 5400, 10800):
            raise ValueError("Unsupported bounded preparation wait")
        self.preparation_seconds = preparation_seconds
        self.run_id, self.docker = run_id, docker
        self.stop = threading.Event()
        self.summary = {'result': 'PENDING', 'samples': 0, 'phases': [],
                        'scope': 'Host observer outside8CPU/8GiB workload budget; instrumented '
                                 'functional/short diagnostic only, never clean capacity. Sequential '
                                 'leaf cgroup/process observations; departed processes unobserved; '
                                 'shared RSS double counts, memory.peak cumulative. No per-request '
                                 'attribution or causal overhead estimate.'}

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True, name='capacity-resources')
        self.thread.start()

    def run(self):
        started, cpu = time.monotonic(), time.thread_time()
        stage = 'topology_inspection'
        try:
            names = ['web-modelos-capacity-' + self.run_id + '-' + role for role in sorted(ROLES)]
            reader = None
            while not self.stop.is_set() and time.monotonic() - started < 600:
                probe = subprocess.run([self.docker, 'inspect', *names], capture_output=True,
                                       text=True, timeout=10, check=False)
                if probe.returncode == 0:
                    inspections = json.loads(probe.stdout)
                    stage = 'identity_validation'
                    try:
                        reader = CapacityResourceReader(self.run_id, dict(zip(sorted(ROLES), inspections, strict=True)))
                    except CapacityContainerPending:
                        self.summary['startup_pending_observations'] = self.summary.get('startup_pending_observations', 0) + 1
                    else:
                        break
                self.stop.wait(1)
            if reader is None:
                raise RuntimeError('Owned service topology not observed')
            self.summary['identities'] = reader.manifest
            written, idle_samples = 0, 0
            phase_started = None
            with (self.output / 'host-service-resources.jsonl').open('x') as stream:
                while not self.stop.is_set():
                    now = time.monotonic()
                    if (now - started >= self.preparation_seconds if phase_started is None
                            else now - phase_started >= 600):
                        raise RuntimeError("Resource observation deadline exceeded")
                    stage = 'phase_read'
                    try:
                        signal = reader.read_phase()
                    except FileNotFoundError:
                        self.stop.wait(.2)
                        continue
                    if phase_started is None:
                        phase_started = time.monotonic()
                        self.summary['preparation_wait_seconds'] = phase_started - started
                    phase = signal['events'][-1]['phase']
                    stage = 'snapshot'
                    row = reader.snapshot(phase)
                    stage = 'phase_confirmation'
                    after = reader.read_phase()
                    row['phase_before'] = signal
                    row['phase_after'] = after
                    stage = 'sample_output'
                    data = json.dumps(row) + '\n'
                    written += len(data.encode())
                    if written > 8 * 1024**2 or self.summary['samples'] >= 600:
                        raise RuntimeError('Resource observation output bound exceeded')
                    stream.write(data)
                    stream.flush()
                    self.summary['samples'] += 1
                    if phase not in self.summary['phases']:
                        self.summary['phases'].append(phase)
                    self.summary['boundaries'] = after
                    if phase == 'idle_after':
                        if self.summary['phases'] != ['before_arrivals', 'arrivals_and_drain', 'idle_after']:
                            raise RuntimeError('Not all workload phases sampled')
                        idle_samples += 1
                        self.summary['idle_after_samples'] = idle_samples
                        if idle_samples == 3:
                            self.summary['result'] = 'OBSERVED_FUNCTIONAL_PHASES_NOT_CAPACITY'
                            return
                    self.stop.wait(.5)
            raise RuntimeError('Resource observation ended before complete phases')
        except Exception as error:
            # Only fixed codes are retained: exception messages can contain paths,
            # provider output or other sensitive details. Never serialize them.
            codes = {
                'Owned capacity container mismatch': 'container_metadata_mismatch',
                'Capacity container cgroup mismatch': 'container_cgroup_mismatch',
                'Distinct container init processes required': 'duplicate_init_pid',
                'Exact cgroup v2 membership required': 'cgroup_membership_invalid',
                'Resource observation deadline exceeded': 'observation_deadline',
            }
            self.summary.update(result='ERROR', error_type=type(error).__name__,
                                error_stage=stage,
                                error_code=codes.get(str(error), 'unclassified'))
        finally:
            self.summary['observer_thread_cpu_seconds'] = time.thread_time() - cpu
            self.summary['elapsed_seconds'] = time.monotonic() - started
            self.summary['observer_process'] = process_row(os.getpid())
            (self.output / 'host-service-resources.summary.json').write_text(json.dumps(self.summary, indent=2) + '\n')

    def close(self):
        self.stop.set()
        self.thread.join(12)
        if self.thread.is_alive():
            raise RuntimeError('Capacity resource observer failed to stop')
        return self.summary
