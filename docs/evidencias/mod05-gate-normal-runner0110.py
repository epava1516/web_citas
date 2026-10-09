import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg
import redis
from cryptography.fernet import Fernet
from psycopg import sql

root = Path('/home/felidae/proyectos/web_modelos')
step = sys.argv[1]
assert step in {'functional', 'short', 'measured'}
out = Path('/tmp/mod05-gate-normal-' + step + '0110')
env = os.environ.copy()
for line in (root / '.env').read_text().splitlines():
    key, sep, value = line.partition('=')
    if sep and key in {'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'MFA_ENCRYPTION_KEY'}:
        env[key] = value.strip().strip('\"\'')
env.update(APP_ENV='development', DB_HOST='127.0.0.1', DB_PORT='55432',
           SAFETY_ENCRYPTION_KEY=Fernet.generate_key().decode(),
           WEB_MODELOS_REFRESH_MODE='normal_worker_beat', PYTHONPATH=str(root) + ':' + str(root / 'tests'), SHELL_KEYBOARD_OUTPUT=str(out))
manifest = json.loads((root/'docs/evidencias/mod05-gate-normal-manifiesto0110.json').read_text())
assert manifest['status'] == 'AUTHORIZED', 'Renewed explicit scope authorization required; no resources created'
assert manifest['refresh_mode'] == 'normal_worker_beat'
broker = redis.Redis.from_url('redis://127.0.0.1:56379/15')
assert broker.dbsize() == 0, 'Owned Redis database 15 must be empty; nothing created'
out.mkdir(exist_ok=False)
source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
hashes = {p.decode(): hashlib.sha256((root / p.decode()).read_bytes()).hexdigest()
          for p in paths if p and (root / p.decode()).is_file()}
(out / 'frozen-manifest.json').write_text(json.dumps({**manifest, 'source_commit': source,
    'step': step, 'source_sha256': hashes, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2))
name = 'promotion_gate_shared_' + uuid.uuid4().hex[:16]
admin = psycopg.connect(dbname=env.get('POSTGRES_DB', 'clasificados'),
    user=env.get('POSTGRES_USER', 'clasificados'), password=env['POSTGRES_PASSWORD'],
    host='127.0.0.1', port=55432, autocommit=True)
result = {'source_commit': source, 'pytest_exit': None, 'cleanup_verified': False}
start = time.perf_counter()
try:
    admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    env['POSTGRES_DB'] = name
    (out / 'owned-databases.json').write_text(json.dumps([name, 'test_' + name]))
    if step == 'measured':
        import xml.etree.ElementTree as ET
        junit = ET.parse('/tmp/mod05-gate-normal-short0110/pytest.xml').getroot()
        prior = json.loads(next(p.get('value') for p in junit.iter('property') if p.get('name') == 'load_summary'))
        assert prior['refresh_mode'] == 'normal_worker_beat' and prior['verdict'] == 'PASS' \
            and prior['diagnostic_continue_contract'], 'Contractual requires complete PASS of the 60 s gate'
    with (out / 'pytest.log').open('w') as log:
        result['pytest_exit'] = subprocess.run([str(root / '.venv/bin/python'), '-m', 'pytest', '-c', str(root / 'pyproject.toml'),
            next(x['selection'] for x in manifest['sequence'] if x['step'] == step), '--maxfail=1',
            '-q', '-o', 'junit_family=xunit1',
            '-p', 'scripts.catalogue_gate_timings',
            '--gate-timings-output=' + str(out / 'test-timings.json'),
            '--junitxml=' + str(out / 'pytest.xml'), '--basetemp=' + str(out / 'pytest-temp')],
            cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
finally:
    result['pytest_seconds'] = time.perf_counter() - start
    owned_file = out / 'owned-databases.json'
    owned_names = json.loads(owned_file.read_text()) if owned_file.exists() else [name, 'test_' + name]
    assert all(db in [name, 'test_' + name] or db.startswith('test_promotion_gate_workers_') for db in owned_names)
    for db in owned_names:
        admin.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(db)))
    result['cleanup_verified'] = not admin.execute('SELECT datname FROM pg_database WHERE datname=ANY(%s)',
                                                   [owned_names]).fetchall()
    admin.close()
    shutil.rmtree(out / 'pytest-temp', ignore_errors=True)
    result['media_removed'] = not (out / 'pytest-temp').exists()
    leftover = list(broker.scan_iter(count=1000))
    if leftover:
        broker.delete(*leftover)
    result['owned_redis_keys_removed_at_end'] = len(leftover)
    result['owned_redis_empty'] = broker.dbsize() == 0
    result['owned_processes_with_output_path_absent'] = not subprocess.run(['pgrep', '-f', str(out)], capture_output=True).stdout
    result['sources_unchanged'] = all((root / p).is_file() and hashlib.sha256((root / p).read_bytes()).hexdigest() == h
                                    for p, h in hashes.items())
    result['artifact_sha256'] = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in out.rglob('*') if p.is_file()}
    (out / 'result.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
