"""Protect the separation between remote acceptance and intrusive diagnostics."""

import importlib
from pathlib import Path

import pytest

from scripts.run_vps_capacity import command


@pytest.mark.parametrize('mode', ['preflight', 'probe', 'measure', 'diagnose'])
@pytest.mark.parametrize('cpu_budget', [4, 8])
def test_vps_modes_obey_existing_runner_contract(mode, cpu_budget, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse_options = importlib.import_module('check_capacity_environment').parse_options
    profiler = tmp_path / 'py-spy'
    profiler.write_text('#!/bin/sh\nexit 0\n')
    profiler.chmod(0o755)
    argv = command(mode, profiler, cpu_budget)
    options, allocations, _ = parse_options(['--owned-controller', *argv[2:]])
    assert options.cpu_budget == cpu_budget
    assert sum(q for q, _ in allocations.values()) + options.controller_cpu_quota == cpu_budget * 100000
    assert sum(m for _, m in allocations.values()) + 128 == 8192
    if mode in ('measure', 'preflight'):
        assert options.delivery_complete == (mode == 'measure')
        assert not options.native_profile
        assert not options.delivery_profile
        assert not options.delivery_profile_full
        assert options.preflight_only == (mode == 'preflight')
    else:
        assert not options.delivery_complete
        assert options.native_profile == Path(profiler).resolve()
        assert options.delivery_profile_full
        assert options.native_probe_only == (mode == 'probe')


@pytest.mark.parametrize('budget', [0, 5, 7, 9, 16])
def test_cpu_comparison_rejects_unapproved_budgets(budget, tmp_path):
    with pytest.raises(ValueError, match='Unsupported CPU budget'):
        command('measure', tmp_path / 'py-spy', budget)


def test_eight_cpu_keeps_memory_workers_and_four_cpu_default(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command('measure', tmp_path / 'py-spy')
    default, original, _ = parse(['--owned-controller', *argv[2:]])
    expanded, eight, _ = parse(['--owned-controller', *argv[2:], '--cpu-budget', '8'])
    assert default.cpu_budget == 4 and default.controller_cpu_quota == 5000
    assert expanded.controller_cpu_quota == 10000
    assert {role: (q * 2, m) for role, (q, m) in original.items()} == eight
    assert expanded.selection_gunicorn == default.selection_gunicorn
    assert expanded.delivery_complete == default.delivery_complete
    assert not expanded.native_profile


def test_eight_cpu_rejects_non_owned_topology(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    with pytest.raises(SystemExit):
        parse(['--cpu-budget', '8'])
