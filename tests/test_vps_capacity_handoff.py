"""Protect the separation between remote acceptance and intrusive diagnostics."""

import importlib
from pathlib import Path

import pytest

from scripts.run_vps_capacity import command


@pytest.mark.parametrize('mode', ['preflight', 'probe', 'measure', 'diagnose'])
def test_vps_modes_obey_existing_runner_contract(mode, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse_options = importlib.import_module('check_capacity_environment').parse_options
    profiler = tmp_path / 'py-spy'
    profiler.write_text('#!/bin/sh\nexit 0\n')
    profiler.chmod(0o755)
    argv = command(mode, profiler)
    options, _, _ = parse_options(['--owned-controller', *argv[2:]])
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
