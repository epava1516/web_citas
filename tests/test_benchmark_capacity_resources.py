"""Fail-closed ownership guards; these tests do not prove a Docker workload."""

import copy
from pathlib import Path

import pytest

from scripts import benchmark_capacity_resources as resources

RUN = '20261022-010000-abcdef12'


def inspection():
    return {'Name': '/web-modelos-capacity-' + RUN + '-pg', 'Id': 'a' * 64,
            'Config': {'Labels': {resources.LABEL: RUN}},
            'State': {'Pid': 123, 'Running': True, 'Paused': False, 'Restarting': False}}


@pytest.mark.parametrize('defect', ['name', 'label', 'id', 'pid', 'bool_pid', 'stopped',
                                   'paused', 'restarting', 'run', 'role'])
def test_foreign_metadata_never_reads_host(monkeypatch, defect):
    data = copy.deepcopy(inspection())
    run, role = RUN, 'pg'
    if defect == 'name':
        data['Name'] = '/foreign'
    elif defect == 'label':
        data['Config']['Labels'][resources.LABEL] = 'foreign'
    elif defect == 'id':
        data['Id'] = 'short'
    elif defect in {'pid', 'bool_pid'}:
        data['State']['Pid'] = 1 if defect == 'pid' else True
    elif defect == 'stopped':
        data['State']['Running'] = False
    elif defect == 'paused':
        data['State']['Paused'] = True
    elif defect == 'restarting':
        data['State']['Restarting'] = True
    elif defect == 'run':
        run = 'foreign'
    else:
        role = 'foreign'

    def forbidden(*args):
        raise AssertionError('Foreign metadata must not read host processes')

    monkeypatch.setattr(resources, 'process_row', forbidden)
    with pytest.raises(ValueError):
        resources.verify_capacity_identity(run, role, data)


def test_cgroup_must_match_full_container_id(monkeypatch):
    monkeypatch.setattr(resources, 'process_row', lambda pid: {'pid': pid, 'start_ticks': 77})
    monkeypatch.setattr(resources, 'group_path', lambda pid: Path('/sys/fs/cgroup/docker-foreign.scope'))
    with pytest.raises(ValueError, match='cgroup mismatch'):
        resources.verify_capacity_identity(RUN, 'pg', inspection())
    group = Path('/sys/fs/cgroup/docker-' + 'a' * 64 + '.scope')
    monkeypatch.setattr(resources, 'group_path', lambda pid: group)
    assert resources.verify_capacity_identity(RUN, 'pg', inspection()) == ({'pid': 123, 'start_ticks': 77}, group)


def test_partial_topology_rejected():
    with pytest.raises(ValueError, match='All six'):
        resources.CapacityResourceReader(RUN, {'pg': inspection()})


@pytest.mark.parametrize('defect', ['pid_reused', 'cgroup_changed', 'phase'])
def test_snapshot_revalidates_identity_before_reading_counters(monkeypatch, defect):
    reader = object.__new__(resources.CapacityResourceReader)
    group = Path('/sys/fs/cgroup/docker-' + 'a' * 64 + '.scope')
    reader.identities = {'pg': ({'pid': 123, 'start_ticks': 77}, group)}
    reader.run_id = RUN
    monkeypatch.setattr(resources, 'process_row', lambda pid: {
        'pid': pid, 'start_ticks': 78 if defect == 'pid_reused' else 77})
    monkeypatch.setattr(resources, 'group_path', lambda pid: (
        Path('/sys/fs/cgroup/foreign') if defect == 'cgroup_changed' else group))

    def forbidden(*args):
        raise AssertionError('Invalid identity or phase must not read counters')

    monkeypatch.setattr(resources, 'read_group', forbidden)
    with pytest.raises(ValueError):
        reader.snapshot('invalid' if defect == 'phase' else 'arrivals_and_drain')


@pytest.mark.parametrize('defect', ['none', 'reused_after_read', 'symlink', 'oversize', 'foreign_run'])
def test_phase_read_is_bounded_and_revalidates_app(monkeypatch, tmp_path, defect):
    import json

    reader = object.__new__(resources.CapacityResourceReader)
    group = Path('/sys/fs/cgroup/docker-' + 'a' * 64 + '.scope')
    reader.identities = {'app': ({'pid': 123, 'start_ticks': 77}, group)}
    reader.run_id = RUN
    root = tmp_path / '123/root/tmp'
    root.mkdir(parents=True)
    path = root / resources.PHASE_PATH.name
    payload = {'run': 'foreign' if defect == 'foreign_run' else RUN,
               'events': [{'phase': 'before_arrivals', 'monotonic': 10.}]}
    data = json.dumps(payload).encode() if defect != 'oversize' else b'x' * (resources.MAX_BYTES + 1)
    if defect == 'symlink':
        target = tmp_path / 'foreign'
        target.write_bytes(data)
        path.symlink_to(target)
    else:
        path.write_bytes(data)
    monkeypatch.setattr(resources, 'Path', lambda value: tmp_path if value == '/proc' else Path(value))
    calls = []

    def identity(pid):
        calls.append(pid)
        return {'start_ticks': 78 if defect == 'reused_after_read' and len(calls) == 2 else 77}

    monkeypatch.setattr(resources, 'process_row', identity)
    monkeypatch.setattr(resources, 'group_path', lambda pid: group)
    if defect == 'none':
        assert reader.read_phase() == payload
        assert calls == [123, 123]
    else:
        with pytest.raises((ValueError, OSError)):
            reader.read_phase()


@pytest.mark.parametrize('foreign', [False, True])
def test_snapshot_reads_exact_leaf_inventory_including_exec_processes(monkeypatch, tmp_path, foreign):
    # PID124 deliberately has no init ancestry: docker exec is covered by leaf membership.
    group = tmp_path / 'leaf'
    group.mkdir()
    (group / 'cgroup.procs').write_text('123\n124\n')
    for name in ('memory.current', 'memory.peak', 'memory.max', 'memory.swap.current',
                 'memory.swap.max', 'cpu.max'):
        (group / name).write_text('1')
    reader = object.__new__(resources.CapacityResourceReader)
    reader.identities = {'app': ({'pid': 123, 'start_ticks': 77}, group)}
    reader.run_id = RUN
    monkeypatch.setattr(resources, 'process_row', lambda pid: {'pid': pid, 'start_ticks': 77})
    monkeypatch.setattr(resources, 'group_path', lambda pid: (
        tmp_path / 'foreign' if pid == 124 and foreign else group))
    monkeypatch.setattr(resources, 'read_group', lambda group: {'cpu_stat': {'usage_usec': 1}})
    if foreign:
        with pytest.raises(ValueError, match='outside owned'):
            reader.snapshot('arrivals_and_drain')
    else:
        result = reader.snapshot('arrivals_and_drain')
        assert [p['pid'] for p in result['services']['app']['processes']] == [123, 124]


@pytest.mark.parametrize('preparation_delay, preparation_budget', [(0, 1800), (700, 1800), (2000, 5400), (6000, 5400), (6000, 10800), (11000, 10800)])
@pytest.mark.parametrize('phases', [
    ['before_arrivals', 'arrivals_and_drain', 'idle_after'], ['before_arrivals', 'idle_after'],
])
def test_observer_requires_all_phases_and_writes_terminal_summary(monkeypatch, tmp_path, phases, preparation_delay, preparation_budget):
    import json
    from types import SimpleNamespace

    monkeypatch.setattr(resources, '__file__', str(tmp_path / 'scripts/reader.py'))
    output = tmp_path / 'artifacts/capacity-environment' / RUN
    output.mkdir(parents=True)
    import os

    (output / 'launcher-started.json').write_text(json.dumps({
        'id': RUN, 'pid': os.getpid(), 'start_ticks': resources.process_row(os.getpid())['start_ticks'],
        'owned': ['web-modelos-capacity-' + RUN + '-' + role for role in resources.ROLES],
    }))
    index = [0]
    clock = resources.time.monotonic
    offset = [0]
    monkeypatch.setattr(resources.time, 'monotonic', lambda: clock() + offset[0])

    reader_attempts = [0]

    class FakeReader:
        def __init__(self, *args):
            reader_attempts[0] += 1
            if reader_attempts[0] == 1:
                raise resources.CapacityContainerPending('Owned capacity container not started')
            self.manifest = {'synthetic_test_only': True}

        def read_phase(self):
            if preparation_delay and not offset[0]:
                offset[0] = preparation_delay
                raise FileNotFoundError('Synthetic delayed fixture preparation')
            return {'run': RUN, 'events': [{'phase': phases[index[0]], 'monotonic': index[0] + 1}]}

        def snapshot(self, phase):
            row = {'phase': phase, 'started_monotonic': index[0] + 1, 'finished_monotonic': index[0] + 1}
            if index[0] < len(phases) - 1:
                index[0] += 1
            return row

    monkeypatch.setattr(resources, 'CapacityResourceReader', FakeReader)
    monkeypatch.setattr(resources.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(
        returncode=0, stdout=json.dumps([{} for _ in resources.ROLES])))
    observer = resources.CapacityResourceObserver(RUN, output, 'docker', preparation_seconds=preparation_budget)
    observer.start()
    observer.thread.join(5)
    result = observer.close()
    assert result['startup_pending_observations'] == 1 and reader_attempts[0] == 2
    if preparation_delay > preparation_budget:
        assert result['result'] == 'ERROR' and result['error_type'] == 'RuntimeError'
        assert result['samples'] == 0
        return
    expected = 'OBSERVED_FUNCTIONAL_PHASES_NOT_CAPACITY' if len(phases) == 3 else 'ERROR'
    assert result['result'] == expected
    assert json.loads((output / 'host-service-resources.summary.json').read_text())['result'] == expected
    assert result['samples'] == len(phases) + (2 if len(phases) == 3 else 0)
    if len(phases) == 3:
        assert result['idle_after_samples'] == 3
    assert result['identities'] == {'synthetic_test_only': True}
    assert result['preparation_wait_seconds'] >= preparation_delay



def test_reader_manifest_contains_only_verified_minimal_identities(monkeypatch):
    inspections = {}
    for index, role in enumerate(sorted(resources.ROLES), 100):
        item = inspection()
        item['Name'] = '/web-modelos-capacity-' + RUN + '-' + role
        item['Id'] = format(index, '064x')
        item['State']['Pid'] = index
        item['Config']['Env'] = ['PRIVATE_TEST_MARKER=must-not-be-retained']
        inspections[role] = item
    monkeypatch.setattr(resources, 'process_row', lambda pid: {'pid': pid, 'start_ticks': pid * 10})
    monkeypatch.setattr(resources, 'group_path', lambda pid: Path(
        '/sys/fs/cgroup/docker-' + format(pid, '064x') + '.scope'))
    reader = resources.CapacityResourceReader(RUN, inspections)
    assert set(reader.manifest) == resources.ROLES
    for role, item in reader.manifest.items():
        assert set(item) == {'run', 'container_id', 'name', 'init_pid', 'init_start_ticks', 'cgroup'}
        assert item['run'] == RUN and item['name'] == inspections[role]['Name']
        assert item['container_id'] == inspections[role]['Id']
        assert item['init_start_ticks'] == item['init_pid'] * 10
    import json

    assert 'PRIVATE_TEST_MARKER' not in json.dumps(reader.manifest)


@pytest.mark.parametrize('message,code', [
    ('Owned capacity container mismatch', 'container_metadata_mismatch'),
    ('Capacity container cgroup mismatch', 'container_cgroup_mismatch'),
    ('PRIVATE_TEST_MARKER=must-not-be-retained', 'unclassified'),
])
def test_observer_records_safe_initialization_failure(monkeypatch, tmp_path, message, code):
    import json
    import threading
    from types import SimpleNamespace

    # Exercise the actual observer loop without Docker or a workload.
    def invalid_reader(*args):
        raise ValueError(message)

    monkeypatch.setattr(resources, 'CapacityResourceReader', invalid_reader)
    monkeypatch.setattr(resources.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=0, stdout=json.dumps([{} for _ in resources.ROLES])))
    observer = resources.CapacityResourceObserver.__new__(resources.CapacityResourceObserver)
    observer.run_id, observer.docker = RUN, 'docker'
    observer.output, observer.stop = tmp_path, threading.Event()
    observer.summary = {'result': 'PENDING', 'samples': 0, 'phases': []}
    observer.run()
    saved = json.loads((tmp_path / 'host-service-resources.summary.json').read_text())
    assert saved['result'] == 'ERROR' and saved['error_type'] == 'ValueError'
    assert saved['error_stage'] == 'identity_validation' and saved['error_code'] == code
    assert saved['samples'] == 0 and 'identities' not in saved
    assert 'PRIVATE_TEST_MARKER' not in json.dumps(saved)
    assert not (tmp_path / 'host-service-resources.jsonl').exists()


@pytest.mark.parametrize('defect', [None, 'foreign', 'paused', 'restarting', 'exited', 'bool_pid'])
def test_created_container_is_pending_only_with_exact_owned_metadata(monkeypatch, defect):
    data = inspection()
    data['State'].update(Status='created', Running=False, Pid=0)
    if defect == 'foreign':
        data['Config']['Labels'][resources.LABEL] = 'foreign'
    elif defect in ('paused', 'restarting'):
        data['State'][defect.title()] = True
    elif defect == 'exited':
        data['State']['Status'] = 'exited'
    elif defect == 'bool_pid':
        data['State']['Pid'] = False

    def forbidden(*args):
        raise AssertionError('Pending or invalid metadata must not read host processes')

    monkeypatch.setattr(resources, 'process_row', forbidden)
    if defect is None:
        with pytest.raises(resources.CapacityContainerPending):
            resources.verify_capacity_identity(RUN, 'pg', data)
    else:
        with pytest.raises(ValueError) as error:
            resources.verify_capacity_identity(RUN, 'pg', data)
        assert type(error.value) is ValueError
