"""Finite warmed directory CPU attribution, never capacity acceptance."""
import cProfile
import io
import json
import os
import pstats
import time
from pathlib import Path

import pytest
from django.core.management import call_command
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_directory_cpu_profile(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_directory_cpu_profile.py' for x in request.config.args):
        pytest.skip('Explicit finite CPU diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    data = populate(10000)
    call_command('refresh_publication_state', stdout=io.StringIO())
    prepare_static_structures()
    routes = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
              '/es/listing/' + data['sample_ids'][0] + '/',
              '/en/listing/' + data['sample_ids'][-1] + '/']
    for route in routes:
        assert client.get(route).status_code == 200
    results = []
    for block in range(2):
        for case, route in enumerate(routes[:4]):
            profiler = cProfile.Profile(timer=time.thread_time)
            profiler.enable()
            try:
                response = client.get(route)
            finally:
                profiler.disable()
            assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
            rows = [{'file': k[0], 'line': k[1], 'function': k[2], 'calls': v[1],
                     'self_cpu_s': v[2], 'cumulative_cpu_s': v[3]}
                    for k, v in pstats.Stats(profiler).stats.items()]
            results.append({'block': block, 'case': case,
                            'profile': sorted(rows, key=lambda r: r['cumulative_cpu_s'], reverse=True)})
    (out / 'directory-cpu-profile.json').write_text(json.dumps(results, indent=2))
    record_property('directory_profile_scope', 'Eight sequential Django client requests, own synthetic10k PG, static and six HTTP-route warmup in same process. cProfile thread CPU overhead, no concurrent admission/socket/Celery or p95. Freshly refreshed state; does not reproduce dirty initial state. Functions overlap; never sum cumulative CPU. No payload/SQL/parameters retained.')
