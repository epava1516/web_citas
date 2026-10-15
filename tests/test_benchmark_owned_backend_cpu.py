"""Counter parsing/identity controls, not PostgreSQL performance evidence."""

from copy import deepcopy

import pytest

from scripts.benchmark_owned_backend_cpu import backend_delta, owned_backend, process_cpu


def test_cpu_parser_handles_parentheses_and_excludes_child_cpu(tmp_path):
    folder = tmp_path / '123'
    folder.mkdir()
    fields = ['S'] + ['0'] * 40
    fields[11], fields[12], fields[13], fields[14], fields[19] = '15', '8', '900', '800', '100'
    (folder / 'stat').write_text('123 (postgres (backend)) ' + ' '.join(fields))
    before = process_cpu(123, tmp_path)
    after = before | {'user_ticks': 25, 'system_ticks': 10, 'monotonic': before['monotonic'] + 2}
    result = backend_delta(before, after, 100)
    assert result['cpu_seconds'] == 0.12
    assert result['elapsed_seconds'] == 2
    for field, value in [('pid', 456), ('start_ticks', 200), ('user_ticks', 0)]:
        with pytest.raises(ValueError):
            backend_delta(before, after | {field: value}, 100)


def test_normal_container_rejected_before_enumerating_processes(monkeypatch):
    run = {'id': '20261015-120000-deadbeef',
           'containers': ['web-modelos-ci-pg-20261015-120000-deadbeef']}
    info = {'Name': '/web-modelos-db-1', 'Config': {'Labels': {}},
            'State': {'Running': True, 'Pid': 123}}
    calls = []
    monkeypatch.setattr('scripts.benchmark_owned_backend_cpu.subprocess.check_output',
                        lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError):
        owned_backend(run, deepcopy(info), 99)
    assert calls == []


def test_backend_mapping_is_scoped_and_rejects_reused_or_moved_pid(monkeypatch):
    from pathlib import Path

    from scripts import benchmark_owned_backend_cpu as observer

    name = 'web-modelos-ci-pg-20261015-120000-deadbeef'
    run = {'id': '20261015-120000-deadbeef', 'containers': [name]}
    info = {'Name': '/' + name, 'Id': 'owned-container-id',
            'Config': {'Labels': {'web-modelos-local-ci-run': run['id']}},
            'State': {'Running': True, 'Pid': 123}}
    calls = []

    def top(command, **kwargs):
        calls.append(command)
        return 'PID\n123\n456\n'

    monkeypatch.setattr(observer.subprocess, 'check_output', top)
    monkeypatch.setattr(observer, 'group_path', lambda pid: Path('/own/owned-container-id'))
    monkeypatch.setattr(observer, 'namespace_pid', lambda pid: {123: 1, 456: 99}[pid])
    monkeypatch.setattr(observer, 'process_cpu', lambda pid: {
        'pid': pid, 'start_ticks': 100, 'user_ticks': 2, 'system_ticks': 1, 'monotonic': 1})
    identity = observer.owned_backend(run, info, 99)
    assert identity['pid'] == 456
    assert calls == [['docker', 'top', name, '-eo', 'pid']]
    assert observer.backend_snapshot(identity)['start_ticks'] == 100
    with pytest.raises(ValueError, match='PID reused'):
        observer.backend_snapshot(identity | {'start_ticks': 200})
    with pytest.raises(ValueError, match='backend changed'):
        observer.backend_snapshot(identity | {'cgroup': '/other'})
