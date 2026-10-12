"""Real restricted-role reconnect probe of the diagnostic, never a capacity run."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from capacity_runtime_role import runtime_role_environment
from django.conf import settings as runtime_settings
from django.db import connection

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not getattr(runtime_settings, 'CAPACITY_NATIVE_PROFILE', False),
                      reason='Requires owned native diagnostic controller'),
]


def test_owned_native_reconnect_probe(settings, record_property):
    with connection.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_stat_statements')
    helper_root = str(Path(__file__).parent)
    script = f'''
import sys,time,json
sys.path.insert(0,{helper_root!r})
import django
django.setup()
from capacity_native_profile import capture
from django.db import connection,close_old_connections
connection.settings_dict['CONN_MAX_AGE']=0
seen=[]
with capture('instrument_probe'):
    for number in range(2):
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid(),current_user')
            pid,user=cursor.fetchone()
            assert user.startswith('capacity_runtime_')
            seen.append(pid)
        time.sleep(.5)
        close_old_connections()
assert seen[0]!=seen[1]
connection.close()
print(json.dumps({{'seen_backends':seen}}))
'''
    with runtime_role_environment('capacity_settings') as credentials:
        environment = os.environ.copy() | credentials
        result = subprocess.run([sys.executable, '-c', script], env=environment,
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, 'Owned native probe child failed'
        expected = json.loads(result.stdout.strip())['seen_backends']
    reports = list(Path('/tmp').glob('capacity-native-instrument_probe-*.pg.json'))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert not report['errors']
    assert [row[1] for row in report['backend_history']] == expected
    assert any(row[1] is not None for row in report['events'])
    assert report['memory_maps'] and report['schema'] == 'capacity-native-v2'
    assert all(type(row[-2]) is bool for row in report['statements_after'])
    record_property('native_probe', json.dumps({'reconnect_verified': True, 'report': report}))
