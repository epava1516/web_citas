"""Failure evidence survives an exited service and a missing sibling."""
import importlib
import json
import subprocess
from pathlib import Path


def test_failed_service_state_capture_keeps_oom_exit_and_continues(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    collect = importlib.import_module('check_capacity_environment').collect_failed_service_states
    observed = []
    expected = {'status': 'exited', 'running': False, 'exit_code': 137,
                'oom_killed': True, 'started_at': 'start', 'finished_at': 'end'}

    def run(command, label, check):
        observed.append(command[-1])
        assert not check
        assert '.Config' not in command[-2] and '.State.Error' not in command[-2]
        if command[-1] == 'missing':
            return subprocess.CompletedProcess(command, 1, '', 'not found')
        if command[-1] == 'timeout':
            raise subprocess.TimeoutExpired(command, 1)
        return subprocess.CompletedProcess(command, 0, json.dumps(expected), '')

    states, errors = collect(run, ['missing', 'timeout', 'stopped', 'sibling'])
    assert observed == ['missing', 'timeout', 'stopped', 'sibling']
    assert states == {'stopped': expected, 'sibling': expected}
    assert errors == {'missing': 'State unavailable', 'timeout': 'TimeoutExpired'}


def test_controller_terminal_state_preserves_identity_without_configuration(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    launcher = importlib.import_module('run_capacity_environment')
    expected = {'id': 'a' * 64, 'status': 'exited', 'running': False,
                'exit_code': 137, 'oom_killed': True, 'started_at': 'start', 'finished_at': 'end'}

    def inspect(command, **options):
        assert command[-1] == 'owned-controller'
        assert '.Config' not in command[-2] and '.State.Error' not in command[-2]
        assert options['timeout'] == 30 and options['check']
        return subprocess.CompletedProcess(command, 0, json.dumps(expected), '')

    monkeypatch.setattr(launcher.subprocess, 'run', inspect)
    assert launcher.controller_terminal_state('docker', 'owned-controller') == expected
    expected['oom_killed'] = 'false'
    assert launcher.controller_terminal_state('docker', 'owned-controller') == {'error_type': 'ValueError'}


def test_controller_terminal_state_failure_does_not_export_stderr(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    launcher = importlib.import_module('run_capacity_environment')

    def inspect(command, **options):
        raise subprocess.CalledProcessError(1, command, stderr='private diagnostic')

    monkeypatch.setattr(launcher.subprocess, 'run', inspect)
    assert launcher.controller_terminal_state('docker', 'missing') == {'error_type': 'CalledProcessError'}
