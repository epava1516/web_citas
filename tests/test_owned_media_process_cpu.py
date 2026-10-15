"""Explicit isolated real media-service SQL/CPU diagnosis; not HTTP capacity."""

import hashlib
import io
import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Revision
from apps.mediafiles.models import Blob, Photo
from apps.mediafiles.services import process
from apps.mediafiles.tasks import process_blob
from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_media_process_cpu(request, settings):
    if not any(str(x).split('::')[0] == 'tests/test_owned_media_process_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit media-service diagnosis only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state', stdout=io.StringIO())
    settings.CELERY_TASK_ALWAYS_EAGER = False
    assert not process_blob.app.conf.task_always_eager
    person = Person.objects.get(individual__username='fixture-v1-individual')
    draft = Revision.objects.create(listing=person.listing, manager_version=person.manager_version)
    raw_image_bytes = raw_image(782134)
    blob = Blob.objects.create(sha256=hashlib.sha256(raw_image_bytes).hexdigest(),
                               original=ContentFile(raw_image_bytes, name='synthetic.jpg'))
    photo = Photo.objects.create(revision=draft, blob=blob)
    connection.close()
    connection.ensure_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_backend_pid(), current_setting(%s)', ['jit'])
        sql_pid, jit = cursor.fetchone()
    identity = owned_backend(run, info, sql_pid)
    records, hottest = [], {}

    def measure(execute, sql, params, many, context):
        before = backend_snapshot(identity)
        wall, cpu = time.perf_counter(), time.thread_time()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed, used = time.perf_counter() - wall, time.thread_time() - cpu
            after = backend_snapshot(identity)
            text = str(sql)
            row = {'fingerprint': hashlib.sha256(text.encode()).hexdigest(),
                   'verb': text.lstrip().split(None, 1)[0] if text.strip() else 'empty',
                   'wall': elapsed, 'python_cpu': used,
                   'backend_cpu': backend_delta(before, after)['cpu_seconds']}
            records.append(row)
            if text.lstrip().upper().startswith('SELECT') and elapsed > hottest.get('wall', -1):
                hottest.update(row, sql=sql, params=params)

    receipt = {'run': run['id'], 'jit': jit, 'backend_identity': identity,
               'scope': 'Real process(blob) function directly, own PostgreSQL and synthetic image. '
                        'No HTTP, concurrency or Celery execution claim. Preparatory model signals '
                        'publish only to owned broker; no worker consumes them. Backend counters100Hz '
                        'and wrappers perturb timing; zero ticks do not mean zero cost.'}
    started, cpu_started = time.perf_counter(), time.thread_time()
    try:
        with connection.execute_wrapper(measure):
            process(blob.pk)
        receipt.update(process_wall=time.perf_counter()-started,
                       process_python_cpu=time.thread_time()-cpu_started)
        blob.refresh_from_db()
        photo.refresh_from_db()
        assert blob.status == 'ready' and photo.comparison_complete
        receipt['completed'] = True
        if hottest:
            with connection.cursor() as cursor:
                cursor.execute('EXPLAIN (FORMAT JSON, SETTINGS) ' + str(hottest['sql']),
                               hottest['params'])
                plan = cursor.fetchone()[0][0]
            def structure(node):
                result = {k: node[k] for k in ['Node Type', 'Relation Name', 'Total Cost',
                                              'Startup Cost', 'Plan Rows'] if k in node}
                if 'Plans' in node:
                    result['Plans'] = [structure(n) for n in node['Plans']]
                return result
            receipt['hottest_select'] = {k:v for k,v in hottest.items() if k not in ['sql','params']}
            receipt['post_execution_estimated_plan'] = structure(plan['Plan'])
            receipt['post_execution_estimated_jit'] = plan.get('JIT')
            receipt['plan_limit'] = 'EXPLAIN without ANALYZE after process; no executed loops/JIT timing proof'
    finally:
        receipt['queries'] = records
        (out / 'media-process-cpu.json').write_text(json.dumps(receipt, indent=2))
