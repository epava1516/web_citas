"""Finite parity/CPU comparison of the exact hot full-Blob selector and EXISTS."""

import hashlib
import io
import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.models import Exists, OuterRef
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings.history import rectification_history_ids
from apps.mediafiles.models import Blob, Photo
from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_media_candidates_cpu(request):
    if not any(str(x).split('::')[0] == 'tests/test_owned_media_candidates_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit hot selector diagnosis only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state', stdout=io.StringIO())
    excluded = Blob.objects.create(sha256='0'*64, status='ready')
    candidates = (Photo.objects.filter(removed_at__isnull=True)
                  .exclude(revision_id__in=rectification_history_ids())
                  .exclude(revision__status='rights-stage')
                  .exclude(rectification_upload__isnull=False))
    native = Blob.objects.filter(status='ready', photos__in=candidates).exclude(pk=excluded.pk).distinct()
    proposed = Blob.objects.filter(status='ready').exclude(pk=excluded.pk).filter(
        Exists(candidates.filter(blob_id=OuterRef('pk'))))
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_backend_pid()')
        pid = cursor.fetchone()[0]
    identity = owned_backend(run, info, pid)
    sql, _ = native.query.sql_with_params()
    results, expected = [], None
    try:
        for block in range(3):
            arms = [('native', native), ('exists', proposed)]
            if block % 2:
                arms.reverse()
            for label, query in arms:
                before = backend_snapshot(identity)
                wall, cpu = time.perf_counter(), time.thread_time()
                blobs = list(query.iterator())  # Full Blob rows and the same cursor strategy.
                elapsed, used = time.perf_counter()-wall, time.thread_time()-cpu
                after = backend_snapshot(identity)
                snapshot = sorted([{
                    f.attname: str(getattr(b,f.attname)) if f.get_internal_type()=='FileField'
                    else getattr(b,f.attname) for f in b._meta.concrete_fields
                } for b in blobs], key=lambda b:str(b['id']))
                encoded = json.dumps(snapshot, sort_keys=True, default=str)
                digest = hashlib.sha256(encoded.encode()).hexdigest()
                if expected is None:
                    expected = digest
                assert digest == expected
                results.append({'block':block,'arm':label,'n':len(blobs),'body_sha256':digest,
                                'wall':elapsed,'python_cpu':used,
                                'backend_cpu':backend_delta(before,after)['cpu_seconds']})
    finally:
        (out/'media-candidates-cpu.json').write_text(json.dumps({
            'results':results,'native_sql_fingerprint':hashlib.sha256(sql.encode()).hexdigest(),
            'photos':Photo.objects.count(),'blobs':Blob.objects.count(),
            'scope':'3 alternating blocks, same full Blob columns and iterator; '
                    'own synthetic DB, exact body hashes. No JIT/session-policy change. '
                    'Counter/wrapper overhead unquantified, backend CPU100Hz; not HTTP capacity '
                    'or complete proof of every exclusion/lifecycle/race.'},indent=2))
    assert len(results)==6
