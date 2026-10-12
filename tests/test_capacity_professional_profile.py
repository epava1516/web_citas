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


def test_professional_argv_keeps_measure_clean(tmp_path):
    argv = command('diagnose', tmp_path / 'py-spy', 8, 'memray', tmp_path)
    assert '--native-profile' not in argv
    assert '--professional-profile' in argv
    assert '--professional-profile' not in command('measure', tmp_path / 'py-spy', 8)
    for mode in ('measure', 'preflight'):
        with pytest.raises(ValueError):
            command(mode, tmp_path / 'py-spy', 8, 'memray', tmp_path)


def test_professional_parser_rejects_mixed_native(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    parse = importlib.import_module('check_capacity_environment').parse_options
    (tmp_path / 'lib/python3.12/site-packages/memray').mkdir(parents=True)
    argv = command('diagnose', tmp_path / 'py-spy', 8, 'memray', tmp_path)[2:]
    options, _, _ = parse(['--owned-controller', *argv])
    assert options.professional_profile == 'memray' and not options.native_profile
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
        result = subprocess.run([sys.executable, '-c', script],
                                env=os.environ.copy() | credentials, capture_output=True,
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
    assert not http_report['errors'] and http_report['native_traces']
    assert http_report['capture_process_cpu_including_tracker_ns'] > 0
    assert not list(Path('/tmp').glob('capacity-professional-instrument_http_probe-*.bin'))
    reports = list(Path('/tmp').glob('capacity-professional-instrument_probe-*.json'))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert not report['errors'] and report['native_traces']
    assert report['capture_process_cpu_including_tracker_ns'] > 0 and report['peak_memory_bytes'] > 0
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
