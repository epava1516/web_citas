"""Protect the separation between remote acceptance and intrusive diagnostics."""

import importlib
from pathlib import Path

import pytest

from scripts.run_vps_capacity import command


@pytest.mark.parametrize('mode', ['beta-http-functional', 'beta-http-short', 'beta-http-contractual'])
def test_beta_http_functional_is_exclusive_bounded_and_never_delivery_measurement(tmp_path, monkeypatch, mode):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command(mode, tmp_path / 'unused', 8, app_image='sha256:' + 'a' * 64)
    options, allocation, _ = parse(['--owned-controller', *argv[2:]])
    assert options.beta_http_functional == (mode == 'beta-http-functional')
    assert options.beta_http_short == (mode == 'beta-http-short')
    assert options.beta_http_contractual == (mode == 'beta-http-contractual')
    assert not options.delivery_complete and not options.preflight_only
    assert allocation['app'] == (350000, 3968)
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    with pytest.raises(ValueError, match='authorized8CPU'):
        command(mode, tmp_path / 'unused', 4)
    others = [[ '--' + other] for other in ('beta-http-functional', 'beta-http-short', 'beta-http-contractual') if other != mode]
    for extra in (['--preflight-only'], ['--delivery-complete'], ['--selection-tcp'], ['--control'], *others):
        with pytest.raises(SystemExit) as rejected:
            parse(['--owned-controller', *argv[2:], *extra])
        assert rejected.value.code == 2


def test_fifteen_upload_calibration_is_functional_only(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command('beta-http-upload-calibration', tmp_path / 'unused', 8)
    options, _, _ = parse(['--owned-controller', *argv[2:]])
    assert options.beta_http_functional and options.beta_http_upload_calibration
    assert not options.beta_http_short and not options.beta_http_contractual
    for flags in (['--beta-http-upload-calibration'],
                  ['--beta-http-upload-calibration', '--beta-http-short'],
                  ['--beta-http-upload-calibration', '--beta-http-contractual'],
                  ['--beta-http-functional', '--beta-http-upload-calibration', '--preflight-only']):
        with pytest.raises(SystemExit) as rejected:
            parse(['--owned-controller', '--object-delivery', '--cpu-budget', '8', *flags])
        assert rejected.value.code == 2
    with pytest.raises(ValueError, match='authorized8CPU'):
        command('beta-http-upload-calibration', tmp_path / 'unused', 4)


@pytest.mark.parametrize('mode', ['preflight', 'measure'])
def test_explicit_immutable_image_reaches_owned_controller(mode, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    image = 'sha256:' + 'a' * 64
    argv = command(mode, tmp_path / 'py-spy', 8, app_image=image)
    options, allocation, _ = parse(['--owned-controller', *argv[2:]])
    assert options.app_image == image and options.cpu_budget == 8
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192


@pytest.mark.parametrize('image', ['latest', 'foreign:tag', 'sha256:1234'])
def test_mutable_or_incomplete_image_override_rejected(image, tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='immutable sha256'):
        command('preflight', tmp_path / 'py-spy', 8, app_image=image)
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    with pytest.raises(SystemExit) as error:
        parse(['--app-image', image])
    assert error.value.code == 2


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


@pytest.mark.parametrize('mode', ['beta-http-functional', 'beta-http-short'])
def test_territorial_kernel_mode_keeps_budget_and_blocks_contractual(tmp_path, monkeypatch, mode):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command(mode, tmp_path / 'unused', 8, territorial=True)
    options, allocation, _ = parse(['--owned-controller', *argv[2:]])
    assert options.beta_http_territorial and (options.beta_http_functional == (mode == 'beta-http-functional'))
    assert options.beta_http_short == (mode == 'beta-http-short')
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    for mode in ('beta-http-contractual', 'beta-http-upload-calibration', 'preflight'):
        with pytest.raises(ValueError, match='functional or preregistered short'):
            command(mode, tmp_path / 'unused', 8, territorial=True)
    for flags in ([], ['--beta-http-contractual'],
                  ['--beta-http-functional', '--beta-http-upload-calibration']):
        with pytest.raises(SystemExit) as rejected:
            parse(['--owned-controller', '--object-delivery', '--cpu-budget', '8',
                   '--beta-http-territorial', *flags])
        assert rejected.value.code == 2


@pytest.mark.parametrize('mode', ['beta-http-functional', 'beta-http-short'])
def test_resource_observer_diagnostics_keep_workload_budget(tmp_path, monkeypatch, mode):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command(mode, tmp_path / 'unused', 8,
                   territorial=True, service_resources=True)
    options, allocation, _ = parse(['--owned-controller', *argv[2:]])
    assert options.beta_http_service_resources and options.beta_http_territorial
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    for mode in ('beta-http-contractual', 'beta-http-upload-calibration', 'preflight'):
        with pytest.raises(ValueError, match='functional or short diagnostic only'):
            command(mode, tmp_path / 'unused', 8, service_resources=True)
    for flags in ([], ['--beta-http-contractual'],
                  ['--beta-http-functional', '--beta-http-upload-calibration']):
        with pytest.raises(SystemExit):
            parse(['--owned-controller', '--object-delivery', '--cpu-budget', '8',
                   '--beta-http-service-resources', *flags])


def test_backlog_requires_exact_small_territorial_observer_mode(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command('beta-http-functional', tmp_path / 'unused', 8,
                   territorial=True, service_resources=True, backlog=True)
    options, _, _ = parse(['--owned-controller', *argv[2:]])
    assert options.beta_http_backlog and options.beta_http_functional
    for kwargs in ({}, {'territorial': True}, {'service_resources': True}):
        with pytest.raises(ValueError, match='Backlog requires'):
            command('beta-http-functional', tmp_path / 'unused', 8, backlog=True, **kwargs)
    for mode in ('beta-http-contractual', 'beta-http-upload-calibration', 'preflight'):
        with pytest.raises(ValueError, match='Backlog requires'):
            command(mode, tmp_path / 'unused', 8, territorial=True, service_resources=True, backlog=True)
    for flags in ([], ['--beta-http-functional'],
                  ['--beta-http-functional', '--beta-http-territorial'],
                  ['--beta-http-functional', '--beta-http-service-resources']):
        with pytest.raises(SystemExit):
            parse(['--owned-controller', '--object-delivery', '--cpu-budget', '8', '--beta-http-backlog', *flags])


@pytest.mark.parametrize('population', [100, 1000, 10000])
def test_scaled_backlog_is_functional_only_and_keeps_budget(tmp_path, monkeypatch, population):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    argv = command('beta-http-functional', tmp_path / 'unused', 8, territorial=True,
                   service_resources=True, backlog=True, backlog_population=population)
    options, allocation, _ = parse(['--owned-controller', *argv[2:]])
    assert options.beta_http_backlog_population == population
    assert options.beta_http_functional and not options.beta_http_short and not options.beta_http_contractual
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    with pytest.raises(ValueError, match='Backlog population'):
        command('beta-http-functional', tmp_path / 'unused', 8, backlog_population=population)
    with pytest.raises(SystemExit):
        parse(['--owned-controller', '--beta-http-backlog-population', str(population)])
    for mode in ('beta-http-short', 'beta-http-contractual', 'beta-http-upload-calibration', 'preflight'):
        with pytest.raises(ValueError, match='Backlog requires'):
            command(mode, tmp_path / 'unused', 8, territorial=True, service_resources=True,
                    backlog=True, backlog_population=population)


@pytest.mark.parametrize('population, expected', [(10, 180), (100, 2400), (1000, 2400), (10000, 9000)])
def test_backlog_watchdog_covers_preparation_without_relaxing_other_commands(tmp_path, monkeypatch, population, expected):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command('beta-http-functional', tmp_path / 'unused', 8, territorial=True,
                   service_resources=True, backlog=True, backlog_population=population)
    options, _, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert controller.command_timeout(options, 'control-pytest') == expected
    assert controller.command_timeout(options, 'django-probe') == 180
    assert controller.app_lifetime(options) > expected
    assert options.beta_http_functional and not options.beta_http_short and not options.beta_http_contractual


@pytest.mark.parametrize('mode, expected, lifetime', [
    ('beta-http-functional', 180, 1800), ('beta-http-short', 2400, 3000),
    ('beta-http-contractual', 3600, 4200), ('beta-http-upload-calibration', 300, 1800),
    ('preflight', 360, 1800),
])
def test_existing_watchdogs_remain_bounded(tmp_path, monkeypatch, mode, expected, lifetime):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command(mode, tmp_path / 'unused', 8)
    options, _, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert controller.command_timeout(options, 'control-pytest') == expected
    assert controller.command_timeout(options, 'django-probe') == 180
    assert controller.app_lifetime(options) == lifetime


@pytest.mark.parametrize('population', [100, 1000, 10000])
def test_mixed_states_require_supported_functional_backlog(tmp_path, monkeypatch, population):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command('beta-http-functional', tmp_path / 'unused', 8, territorial=True,
                   service_resources=True, backlog=True, backlog_population=population, mixed_states=True)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_mixed_states and options.beta_http_backlog_population==population
    assert controller.command_timeout(options, 'control-pytest') == (18000 if population == 10000 else 2400)
    assert controller.app_lifetime(options) == (18600 if population == 10000 else 3000)
    assert controller.command_timeout(options, 'django-probe') == 180
    assert sum(q for q, _ in allocation.values())+options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values())+128 == 8192
    for invalid_population in (10, 100000):
        with pytest.raises(ValueError, match='Mixed states'):
            command('beta-http-functional', tmp_path / 'unused', 8, territorial=True,
                    service_resources=True, backlog=True, backlog_population=invalid_population, mixed_states=True)
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', '--object-delivery', '--cpu-budget', '8',
                                      '--beta-http-functional', '--beta-http-territorial',
                                      '--beta-http-service-resources', '--beta-http-backlog',
                                      '--beta-http-backlog-population', str(invalid_population), '--beta-http-mixed-states'])
    with pytest.raises(ValueError, match='Mixed states'):
        command('beta-http-functional', tmp_path / 'unused', 8, mixed_states=True)
    for mode in ('beta-http-short', 'beta-http-contractual', 'beta-http-upload-calibration', 'preflight'):
        with pytest.raises(ValueError, match='Backlog requires'):
            command(mode, tmp_path / 'unused', 8, territorial=True, service_resources=True,
                    backlog=True, backlog_population=100, mixed_states=True)


@pytest.mark.parametrize('population', [100, 1000, 10000])
def test_committed_mixture_is_exclusive_functional_and_preserves_owned_budget(tmp_path, monkeypatch, population):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command('beta-http-functional', tmp_path / 'unused', 8, territorial=True,
                   committed_mixed=True, committed_population=population)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_committed_mixed and options.beta_http_committed_population == population
    assert not options.beta_http_backlog and not options.beta_http_mixed_states
    assert not options.beta_http_short and not options.beta_http_contractual
    assert controller.command_timeout(options, 'control-pytest') == (18000 if population==10000 else 2400)
    assert controller.app_lifetime(options) == (18600 if population==10000 else 3000)
    assert controller.command_timeout(options, 'django-probe') == 180
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    for mode in ('beta-http-short', 'beta-http-contractual', 'beta-http-upload-calibration', 'preflight'):
        with pytest.raises(ValueError, match='Committed mixture'):
            command(mode, tmp_path / 'unused', 8, territorial=True, committed_mixed=True)
    for invalid in ({'territorial': False}, {'backlog': True}, {'mixed_states': True}):
        kwargs = {'territorial': True, 'committed_mixed': True} | invalid
        with pytest.raises(ValueError, match='Committed mixture'):
            command('beta-http-functional', tmp_path / 'unused', 8, **kwargs)
    for flag in ('--beta-http-backlog', '--beta-http-mixed-states', '--beta-http-upload-calibration',
                 '--beta-http-short', '--beta-http-contractual'):
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *argv[2:], flag])
    for invalid in (10, 100000):
        with pytest.raises(ValueError, match='Committed population'):
            command('beta-http-functional', tmp_path / 'unused', 8, territorial=True,
                    committed_mixed=True, committed_population=invalid)
    with pytest.raises(ValueError, match='Committed population'):
        command('beta-http-functional', tmp_path / 'unused', 8, committed_population=1000)
    with pytest.raises(SystemExit):
        controller.parse_options(['--beta-http-committed-population', '1000'])


def test_committed_short_requires_full_population_and_preserves_acceptance_budget(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command('beta-http-short', tmp_path / 'unused', 8, territorial=True,
                   committed_mixed=True, committed_population=10000)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_short and not options.beta_http_functional and not options.beta_http_contractual
    assert options.beta_http_committed_population == 10000 and options.beta_http_committed_mixed
    assert not options.beta_http_service_resources and not options.beta_http_backlog
    assert controller.command_timeout(options, 'control-pytest') == 18000
    assert controller.app_lifetime(options) == 18600
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    for population in (100, 1000):
        with pytest.raises(ValueError, match='Committed mixture'):
            command('beta-http-short', tmp_path / 'unused', 8, territorial=True,
                    committed_mixed=True, committed_population=population)
        small = argv[2:].copy()
        small[small.index('--beta-http-committed-population') + 1] = str(population)
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *small])


@pytest.mark.parametrize('mode', ['beta-http-short', 'beta-http-contractual'])
def test_committed_full_load_modes_keep_population_and_budget(tmp_path, monkeypatch, mode):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command(mode, tmp_path / 'unused', 8, territorial=True,
                   committed_mixed=True, committed_population=10000)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_contractual == (mode == 'beta-http-contractual')
    assert options.beta_http_short == (mode == 'beta-http-short')
    assert not options.beta_http_functional
    assert options.beta_http_territorial and options.beta_http_committed_mixed
    assert options.beta_http_committed_population == 10000
    assert not options.beta_http_service_resources and not options.beta_http_backlog
    assert controller.command_timeout(options, 'control-pytest') == 18000
    assert controller.app_lifetime(options) == 18600
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    for population in (100, 1000):
        with pytest.raises(ValueError, match='Committed mixture'):
            command(mode, tmp_path / 'unused', 8, territorial=True,
                    committed_mixed=True, committed_population=population)
        small = argv[2:].copy()
        small[small.index('--beta-http-committed-population') + 1] = str(population)
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *small])
    if mode == 'beta-http-contractual':
        with pytest.raises(ValueError, match='Service resources'):
            command(mode, tmp_path / 'unused', 8, territorial=True, committed_mixed=True,
                    committed_population=10000, service_resources=True)
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *argv[2:], '--beta-http-service-resources'])



def test_combined_filters_are_exclusive_functional100_with_unchanged_quotas(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command('beta-http-functional', tmp_path/'unused', 8,
                   territorial=True, combined_filters=True)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_combined_filters and options.beta_http_functional
    assert not options.beta_http_service_resources and not options.beta_http_committed_mixed
    assert allocation['app'] == (350000, 3968)
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    assert controller.command_timeout(options, 'control-pytest') == 2400
    assert controller.app_lifetime(options) == 3000
    for mode in ('preflight', 'measure', 'beta-http-short', 'beta-http-contractual', 'beta-http-upload-calibration'):
        with pytest.raises(ValueError, match='Combined filters'):
            command(mode, tmp_path/'unused', 8, territorial=True, combined_filters=True)
    for extra in ({'territorial': False}, {'committed_mixed': True}, {'backlog': True},
                  {'mixed_states': True}, {'service_resources': True}):
        with pytest.raises(ValueError, match='Combined filters'):
            command('beta-http-functional', tmp_path/'unused', 8,
                    **({'territorial': True, 'combined_filters': True} | extra))
    for flag in ('--beta-http-short', '--beta-http-contractual', '--beta-http-service-resources',
                 '--beta-http-backlog', '--beta-http-committed-mixed', '--beta-http-upload-calibration'):
        with pytest.raises(SystemExit) as rejected:
            controller.parse_options(['--owned-controller', *argv[2:], flag])
        assert rejected.value.code == 2


def test_generator_diagnostic_requires_combined100_and_remains_nonacceptance(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    with pytest.raises(ValueError, match='Generator diagnostic'):
        command('beta-http-functional', tmp_path/'unused', 8, generator_diagnostic=True)
    with pytest.raises(SystemExit):
        controller.parse_options(['--owned-controller', '--cpu-budget', '8', '--beta-http-functional',
                                  '--beta-http-generator-diagnostic'])
    argv = command('beta-http-functional', tmp_path/'unused', 8, territorial=True,
                   combined_filters=True, generator_diagnostic=True)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_generator_diagnostic and options.beta_http_combined_filters
    assert controller.command_timeout(options, 'control-pytest') == 2400
    assert allocation['app'] == (350000,3968)


def test_generator_observer_retains_per_emission_boundaries_and_policy(tmp_path):
    from capacity_combined_filters import observe_generator

    from scripts.benchmark_async_transport import POLICY

    async def fetch(path, **kwargs):
        return {'status':200,'unexpected':False,'timeout':False,'bytes':1}

    proof = {}
    result = observe_generator(fetch, ['/es/'], proof=proof, output=tmp_path/'observer.json',
                               duration=.15, rps=20, upload_specs=[])
    assert result['counts']['scheduled'] == result['counts']['successful'] == 3
    assert result['policy'] == POLICY
    assert result['scheduler_trace']['emission_and_validity_policy_unchanged']
    for row in result['samples']:
        assert row['scheduled_at'] <= row['scheduler_awoke_at'] <= row['task_queued_at'] <= row['emitted_at']
    observation = proof['generator_diagnostic']
    assert observation['iterations'] > 0 and len(observation['events']) <= 256
    assert 'DIAGNOSTIC ONLY' in observation['scope']
    assert observation['load']['verdict'] == result['verdict']
    assert observation['load']['invalid_reasons'] == result['invalid_reasons']


@pytest.mark.parametrize('population', [100, 1000, 10000])
def test_combined_population_reaches_controller_without_relaxing_exclusivity(tmp_path, monkeypatch, population):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command('beta-http-functional', tmp_path/'unused', 8, territorial=True,
                   combined_filters=True, combined_population=population)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_combined_population == population
    assert allocation['app'] == (350000, 3968)
    assert controller.command_timeout(options, 'control-pytest') == (18000 if population == 10000 else 2400)
    assert controller.app_lifetime(options) == (18600 if population == 10000 else 3000)
    if population != 100:
        with pytest.raises(ValueError, match='Combined population'):
            command('beta-http-functional', tmp_path/'unused', 8, combined_population=population)
        with pytest.raises(ValueError, match='Generator diagnostic'):
            command('beta-http-functional', tmp_path/'unused', 8, territorial=True,
                    combined_filters=True, combined_population=population, generator_diagnostic=True)
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *argv[2:], '--beta-http-generator-diagnostic'])
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', '--beta-http-combined-population', str(population)])
    if population != 10000:
        with pytest.raises(ValueError, match='Combined filters'):
            command('beta-http-short', tmp_path/'unused', 8, territorial=True,
                    combined_filters=True, combined_population=population)


@pytest.mark.parametrize('population,listing_pairs,search_pairs', [(100, 8, 10), (1000, 14, 16), (10000, 14, 16)])
def test_combined_cycle_covers_every_selected_page_with_balanced_locales(monkeypatch, population, listing_pairs, search_pairs):
    from collections import Counter

    import capacity_combined_filters as combined

    specs = []
    for category, pairs in (('', listing_pairs), ('photography', search_pairs)):
        for page in range(pairs):
            for locale in ('es', 'en'):
                specs.append({'path': f'/{locale}/?q={category}&page={page+1}'})
    monkeypatch.setattr(combined, 'verify_owned_fixture', lambda: None)
    monkeypatch.setattr(combined, 'cases', lambda dataset: specs)
    details = ['/es/listing/first/', '/en/listing/last/']
    oracle, routes = combined.plan({'published': population}, details)
    assert oracle == specs
    assert set(routes) == {row['path'] for row in specs} | set(details)
    emitted = [routes[i % len(routes)] for i in range(60 if population == 100 else 120)]
    assert set(emitted) == set(routes)
    assert Counter(path.split('/')[1] for path in emitted) == {'es': len(emitted)//2, 'en': len(emitted)//2}
    kinds = Counter('detail' if '/listing/' in path else 'search' if 'q=photography' in path else 'listing' for path in emitted)
    assert set(kinds.values()) == {len(emitted)//3}


@pytest.mark.parametrize('mode', ['beta-http-short', 'beta-http-contractual'])
def test_combined_full_load10000_reaches_controller_with_unchanged_budget(tmp_path, monkeypatch, mode):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    controller = importlib.import_module('check_capacity_environment')
    argv = command(mode, tmp_path/'unused', 8, territorial=True,
                   combined_filters=True, combined_population=10000)
    options, allocation, _ = controller.parse_options(['--owned-controller', *argv[2:]])
    assert options.beta_http_short == (mode == 'beta-http-short')
    assert options.beta_http_contractual == (mode == 'beta-http-contractual')
    assert not options.beta_http_functional
    assert options.beta_http_combined_population == 10000 and options.beta_http_combined_filters
    assert allocation['app'] == (350000, 3968)
    assert sum(q for q, _ in allocation.values()) + options.controller_cpu_quota == 800000
    assert sum(m for _, m in allocation.values()) + 128 == 8192
    assert controller.command_timeout(options, 'control-pytest') == 18000
    assert controller.app_lifetime(options) == 18600
    for population in (100, 1000):
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *argv[2:],
                                      '--beta-http-combined-population', str(population)])
    for extra in (('--beta-http-contractual' if mode == 'beta-http-short' else '--beta-http-short'), '--beta-http-generator-diagnostic',
                  '--beta-http-service-resources', '--beta-http-backlog',
                  '--beta-http-committed-mixed', '--beta-http-upload-calibration'):
        with pytest.raises(SystemExit):
            controller.parse_options(['--owned-controller', *argv[2:], extra])
    for population in (100, 1000):
        with pytest.raises(ValueError, match='Combined filters'):
            command(mode, tmp_path/'unused', 8, territorial=True,
                    combined_filters=True, combined_population=population)
    with pytest.raises(ValueError, match='Generator diagnostic'):
        command(mode, tmp_path/'unused', 8, territorial=True, combined_filters=True,
                combined_population=10000, generator_diagnostic=True)
