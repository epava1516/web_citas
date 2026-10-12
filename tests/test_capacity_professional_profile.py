"""Separation tests plus an explicitly selected real restricted-role instrument probe."""

import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_vps_capacity import command


@pytest.mark.parametrize('kind', ['memray', 'scalene'])
def test_professional_argv_keeps_measure_clean(tmp_path, kind):
    argv = command('diagnose', tmp_path / 'py-spy', 8, kind, tmp_path)
    assert '--native-profile' not in argv
    assert '--professional-profile' in argv
    assert '--professional-profile' not in command('measure', tmp_path / 'py-spy', 8)
    for mode in ('measure', 'preflight'):
        with pytest.raises(ValueError):
            command(mode, tmp_path / 'py-spy', 8, kind, tmp_path)


@pytest.mark.parametrize('kind', ['memray', 'scalene'])
def test_professional_parser_rejects_mixed_native(tmp_path, monkeypatch, kind):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    (tmp_path / f'lib/python3.12/site-packages/{kind}').mkdir(parents=True)
    argv = command('diagnose', tmp_path / 'py-spy', 8, kind, tmp_path)[2:]
    options, _, _ = parse(['--owned-controller', *argv])
    assert options.professional_profile == kind and not options.native_profile
    for extra in (['--native-profile', str(tmp_path / 'py-spy')], ['--selection-profile'],
                  ['--source-profile'], ['--diagnose'], ['--delivery-complete']):
        with pytest.raises(SystemExit):
            parse(['--owned-controller', *argv, *extra])


@pytest.mark.django_db(transaction=True)
def test_owned_professional_probe(settings, record_property):
    if not getattr(settings, 'CAPACITY_PROFESSIONAL_PROFILE', None):
        pytest.skip('Requires explicit own professional instrument probe')
    from capacity_runtime_role import runtime_role_environment

    helper = str(Path(__file__).parent)
    script = f'''
import sys,json
sys.path.insert(0,{helper!r})
import django
django.setup()
from django.db import connection,close_old_connections
from capacity_professional_profile import capture
connection.settings_dict['CONN_MAX_AGE']=0
seen=[]
with capture('instrument_probe'):
    for index in range(2):
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid(),current_user')
            pid,user=cursor.fetchone()
            assert user.startswith('capacity_runtime_')
            seen.append(pid)
        data=[bytes(8192) for _ in range(64)]
        close_old_connections()
assert seen[0]!=seen[1]
connection.close()
print(json.dumps({{'reconnect_verified':True}}))
'''
    with runtime_role_environment('capacity_settings') as credentials:
        environment = os.environ.copy() | credentials
        child_command = [sys.executable, '-c', script]
        if settings.CAPACITY_PROFESSIONAL_PROFILE == 'scalene':
            app_site = str(Path(sys.prefix) / 'lib/python3.12/site-packages')
            tool_site = str(Path(settings.CAPACITY_DIAGNOSTIC_TOOLS_VENV) / 'lib/python3.12/site-packages')
            environment['PYTHONPATH'] = environment.get('PYTHONPATH', '') + ':' + app_site + ':' + tool_site
            program = Path('/tmp/capacity-professional-probe-child.py')
            program.write_text(script)
            child_command = [sys.executable, '-m', 'scalene', 'run', '--cpu-only', '--off',
                             '--profile-all', '--profile-only', 'capacity_professional_profile',
                             '-o', '/tmp/scalene-probe-child.json', str(program)]
        result = subprocess.run(child_command, env=environment, capture_output=True,
                                text=True, timeout=45)
        child_reports = {path.name: json.loads(path.read_text()) for path in
                         Path('/tmp').glob('capacity-professional-instrument_probe-*.json')}
        record_property('professional_probe_child', json.dumps({
            'exit_code': result.returncode, 'reports': child_reports,
            'stderr_bytes': len(result.stderr.encode()),
            'stderr_sha256': hashlib.sha256(result.stderr.encode()).hexdigest(),
            'memray_message_present': 'Memray' in result.stderr,
        }))
        assert result.returncode == 0, 'Restricted-role Memray probe child failed'
    # Exercise the actual Gunicorn WSGI wrapper over HTTP, rather than proving only Tracker import.
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    from capacity_gunicorn import server

    with server(settings, record_property) as endpoint:
        request = Request(endpoint.url + '/health/', headers={'X-Capacity-Profile': 'instrument_http_probe'})
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            assert response.status == 200
            response.read(1024 * 1024)
    http_reports = list(Path('/tmp').glob('capacity-professional-instrument_http_probe-*.json'))
    assert len(http_reports) == 1
    http_report = json.loads(http_reports[0].read_text())
    assert not http_report['errors'] and http_report['status'] == 'COMPLETE'
    assert http_report['capture_process_cpu_including_tracker_ns'] > 0
    assert not list(Path('/tmp').glob('capacity-professional-instrument_http_probe-*.bin'))
    reports = list(Path('/tmp').glob('capacity-professional-instrument_probe-*.json'))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert not report['errors'] and report['status'] == 'COMPLETE'
    assert report['capture_process_cpu_including_tracker_ns'] > 0
    if settings.CAPACITY_PROFESSIONAL_PROFILE == 'memray':
        assert report['native_traces'] and http_report['native_traces'] and report['peak_memory_bytes'] > 0
    else:
        profile = json.loads(Path('/tmp/capacity-professional-scalene-all.json').read_text())
        assert profile['files'] and any(file['percent_cpu_time'] > 0 for file in profile['files'].values())
        assert report['samples_flushed'] and http_report['samples_flushed']
    assert not list(Path('/tmp').glob('capacity-professional-instrument_probe-*.bin'))
    record_property('professional_probe', json.dumps({'instrument_verified': True, 'http_hook_verified': True, 'report': report, 'http_report': http_report}))


def test_professional_flow_excludes_legacy_profiles(settings, monkeypatch):
    import capacity_delivery_flow as flow

    settings.CAPACITY_PROFESSIONAL_PROFILE = 'memray'
    settings.CAPACITY_NATIVE_PROFILE = False
    def forbidden(*args, **kwargs):
        raise AssertionError('Legacy profiler called in professional mode')
    monkeypatch.setattr(flow.cProfile, 'Profile', forbidden)
    monkeypatch.setattr(flow, 'validation_profile', forbidden)
    metrics = {'diagnostic': True}
    assert flow.measured(metrics, 'probe', lambda: 123) == 123
    assert not metrics.get('profiles')
    assert flow.post_validation_profile(None, None, diagnostic=True)['status'] == 'disabled'


@pytest.mark.parametrize('status', ['COMPLETE', 'FAIL'])
def test_professional_sampling_stops_after_invalid_capture(tmp_path, status):
    import ast
    import time
    from types import SimpleNamespace

    tree = ast.parse(Path(__file__).with_name('capacity_delivery_flow.py').read_text())
    function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'sampled')

    def post(*args, **kwargs):
        (tmp_path / 'capacity-professional-coverage_page_read-owned.json').write_text(
            json.dumps({'status': status, 'errors': [] if status == 'COMPLETE' else ['SummaryLimit']}))
        return SimpleNamespace(seconds=1.5, interval=[10, 11.5], body=b'ok', status=200,
                               headers={'Cache-Control': 'no-store'}, stages=[])

    namespace = {'HEADER': 'unused', 'runtime_settings': SimpleNamespace(CAPACITY_PROFESSIONAL_PROFILE='memray'),
                 'Path': lambda _: tmp_path, 'post': post, 'json': json, 'time': time}
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<professional-flow-test>', 'exec'), namespace)
    metrics = {}
    barrier = SimpleNamespace(wait=lambda **kwargs: None)
    if status == 'FAIL':
        with pytest.raises(AssertionError, match='SummaryLimit'):
            namespace['sampled'](metrics, 'coverage_page_read', barrier, None, '', '', {}, profile=True)
        assert not metrics
    else:
        assert namespace['sampled'](metrics, 'coverage_page_read', barrier, None, '', '', {}, profile=True) == b'ok'
        assert metrics['coverage_page_read_profiled_seconds'] == [1.5]
