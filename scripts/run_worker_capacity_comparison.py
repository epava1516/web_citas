import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import psycopg
from cryptography.fernet import Fernet
from psycopg import sql

root = Path('/home/felidae/proyectos/web_modelos')
out = Path('/tmp/worker-capacity-4-vs-6-ready0110')
out.mkdir(exist_ok=False)
env = os.environ.copy()
for line in (root / '.env').read_text().splitlines():
    key, sep, value = line.partition('=')
    if sep and key in {'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'MFA_ENCRYPTION_KEY'}:
        env[key] = value.strip().strip('\"\'')
env.update(APP_ENV='development', DB_HOST='127.0.0.1', DB_PORT='55432',
           SAFETY_ENCRYPTION_KEY=Fernet.generate_key().decode(),
           PYTHONPATH=str(root), WORKER_COMPARISON_OUTPUT=str(out))
manifest = json.loads((root/'docs/evidencias/comparacion-capacidad-4-vs-6-manifiesto0110.json').read_text())
source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
paths = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
hashes = {p.decode(): hashlib.sha256((root / p.decode()).read_bytes()).hexdigest()
          for p in paths if p and (root / p.decode()).is_file()}
(out / 'frozen-manifest.json').write_text(json.dumps({**manifest, 'source_commit': source,
    'source_sha256': hashes, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2))
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
    with (out / 'pytest.log').open('w') as log:
        result['pytest_exit'] = subprocess.run([str(root / '.venv/bin/python'), '-m', 'pytest',
            *manifest['selection'], '--maxfail=1',
            '-q',
            '-p', 'scripts.catalogue_gate_timings',
            '--gate-timings-output=' + str(out / 'test-timings.json'),
            '--junitxml=' + str(out / 'pytest.xml'), '--basetemp=' + str(out / 'pytest-temp')],
            cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
finally:
    result['pytest_seconds'] = time.perf_counter() - start
    for db in json.loads((out / 'owned-databases.json').read_text())[::-1]:
        admin.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(db)))
    result['cleanup_verified'] = not admin.execute('SELECT datname FROM pg_database WHERE datname=ANY(%s)',
                                                   [json.loads((out / 'owned-databases.json').read_text())]).fetchall()
    admin.close()
    shutil.rmtree(out / 'pytest-temp', ignore_errors=True)
    result['media_removed'] = not (out / 'pytest-temp').exists()
    result['sources_unchanged'] = all((root / p).is_file() and hashlib.sha256((root / p).read_bytes()).hexdigest() == h
                                    for p, h in hashes.items())
    result['artifact_sha256'] = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in out.rglob('*') if p.is_file()}
    (out / 'result.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
