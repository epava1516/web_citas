"""Explicit isolated request diagnostic; no capacity claim or queue worker."""
import cProfile
import io
import json
import os
import pstats
import time
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401

from apps.core.models import User
from apps.listings.models import Revision
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.tasks import process_blob
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_upload_warm_profile(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_upload_warm_profile.py' for x in request.config.args):
        pytest.skip('Explicit request diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    queued = []
    monkeypatch.setattr(process_blob, 'delay', lambda pk: queued.append(pk))
    dataset = populate(10000)
    call_command('refresh_publication_state', stdout=io.StringIO())
    routes = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
              '/es/listing/' + dataset['sample_ids'][0] + '/',
              '/en/listing/' + dataset['sample_ids'][-1] + '/']
    probes = [{'index': i, 'status': client.get(route).status_code} for i, route in enumerate(routes)]
    assert all(row['status'] == 200 for row in probes)
    assert client.get('/es/account/login/').status_code == 200
    record_property('warm_probes', json.dumps(probes))
    user = User.objects.get(username='fixture-v1-individual')
    client.force_login(user)
    from apps.core.models import Person
    person = Person.objects.get(individual=user)
    draft = Revision.objects.create(listing=person.listing, manager_version=person.manager_version)
    call_command('refresh_publication_state', stdout=io.StringIO())
    raw = raw_image(782134)
    with connection.cursor() as cursor:
        cursor.execute("SET track_functions = 'all'")
        def snapshot():
            cursor.execute('SELECT pg_stat_force_next_flush()')
            cursor.execute('SELECT pg_stat_clear_snapshot()')
            cursor.execute("SELECT calls,total_time,self_time FROM pg_stat_user_functions WHERE funcid='listings_publication_mark(uuid[])'::regprocedure")
            return cursor.fetchone() or (0, 0, 0)
        before = snapshot()
        wall, cpu = time.perf_counter(), time.thread_time()
        profiler = cProfile.Profile(timer=time.thread_time)
        profiler.enable()
        try:
            response = upload(client, draft, raw)
        finally:
            profiler.disable()
        stats = pstats.Stats(profiler)
        profile_rows = [{"file": key[0], "line": key[1], "function": key[2], "primitive_calls": value[0], "calls": value[1], "self_cpu_s": value[2], "cumulative_cpu_s": value[3]} for key, value in stats.stats.items()]
        profile_rows.sort(key=lambda x: x["cumulative_cpu_s"], reverse=True)
        (out / "upload-warm-profile.json").write_text(json.dumps(profile_rows, indent=2))
        elapsed, used = time.perf_counter()-wall, time.thread_time()-cpu
        after = snapshot()
        cursor.execute("SET track_functions = 'none'")
    assert response.status_code == 302
    assert len(queued) == 1
    delta = dict(zip(['calls','total_ms','self_ms'], [a-b for a,b in zip(after,before)]))
    assert delta['calls'] > 0
    record_property('upload_warm_profile', json.dumps({'request_wall_ms': elapsed*1000, 'request_caller_cpu_ms': used*1000, 'mark': delta, 'status': response.status_code, 'queued_blob_tasks':len(queued)}))
    record_property('limits', 'Own synthetic PG10k. Django test client, one upload using capacity image seed. Async task dispatch replaced with recording; no Celery/Beat, HTTP socket, concurrent readers or p95. cProfile thread CPU instrumentation enabled; cumulative calls overlap, never sum. No payload/SQL/parameters retained. Six capacity routes plus login GET warmed in same client process. This is stronger per-process warming than unassigned requests across four Gunicorn workers; not equivalent topology. No causal capacity proof.')
