"""Keep SQL-plan diagnostics separate from profilers and acceptance."""

import importlib
from pathlib import Path

import pytest

from scripts.run_vps_capacity import command


@pytest.mark.parametrize('target', [64, 304])
def test_sql_plan_mode_is_exclusive(target, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command('diagnose', Path('/unused/py-spy'), 8, sql_plan_target=target)
    assert '--native-profile' not in argv and '--professional-profile' not in argv
    options, _, _ = parse(['--owned-controller', *argv[2:]])
    assert options.sql_plan_target == target
    for extra in [['--source-profile'], ['--delivery-complete'], ['--preflight-only'],
                  ['--native-profile', '/unused/py-spy'], ['--professional-profile', 'scalene']]:
        with pytest.raises(SystemExit):
            parse(['--owned-controller', *argv[2:], *extra])
    for mode in ['measure', 'preflight', 'probe']:
        with pytest.raises(ValueError):
            command(mode, Path('/unused'), 8, sql_plan_target=target)
    with pytest.raises(ValueError):
        command('diagnose', Path('/unused'), 8, 'memray', sql_plan_target=target)
    assert '--sql-plan-target' not in command('measure', Path('/unused'), 8)
