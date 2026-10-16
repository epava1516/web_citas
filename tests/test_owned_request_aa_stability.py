"""Identical-code A/A control separating new and warmed physical connections."""
import gc
import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_request_aa_stability(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_request_aa_stability.py' for x in request.config.args):
        pytest.skip('Explicit owned identical-code A/A only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out/'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    routes = ['/es/', '/en/?q=synthetic']
    signatures = {}
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200
        signatures[route] = hashlib.sha256(response.content).hexdigest()
    rows, preparation = [], []
    for mode in ['new_connection', 'persistent_warmed']:
        for route in routes:
            for block in range(3):
                for arm in (['A', 'B'] if block % 2 == 0 else ['B', 'A']):
                    connection.close()
                    if mode == 'persistent_warmed':
                        for _ in range(6):
                            response = client.get(route)
                            assert response.status_code == 200
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT pg_backend_pid(), (SELECT count(*) FROM pg_prepared_statements)')
                            warm_pid, warm_plans = cursor.fetchone()
                        preparation.append(dict(mode=mode, route=route, block=block, arm=arm,
                                                backend_pid=warm_pid, prepared_statements=warm_plans))
                    seen = []
                    for repeat in range(4):
                        if mode == 'new_connection':
                            connection.close()
                        observed = {'calls':0, 'backend_pids':set()}
                        def counted(execute, sql, params, many, context):
                            observed['calls'] += 1
                            observed['backend_pids'].add(context['connection'].connection.info.backend_pid)
                            return execute(sql, params, many, context)
                        before_gc = gc.get_stats()
                        wall, cpu = time.perf_counter(), time.thread_time()
                        with connection.execute_wrapper(counted):
                            response = client.get(route)
                        elapsed, used = time.perf_counter()-wall, time.thread_time()-cpu
                        assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                        assert hashlib.sha256(response.content).hexdigest() == signatures[route]
                        assert len(observed['backend_pids']) == 1
                        pid = observed['backend_pids'].pop()
                        seen.append(pid)
                        if mode == 'persistent_warmed':
                            assert pid == warm_pid
                        rows.append(dict(mode=mode, route=route, block=block, arm=arm, repeat=repeat,
                            wall=elapsed, cpu=used, sql=observed['calls'], backend_pid=pid,
                            gc_collections=[a['collections']-b['collections'] for a,b in zip(gc.get_stats(),before_gc,strict=True)]))
                    if mode == 'new_connection':
                        assert len(set(seen)) == 4
    assert len(rows) == 96
    comparisons=[]
    for mode in ['new_connection', 'persistent_warmed']:
        for route in routes:
            for block in range(3):
                medians={arm:statistics.median(r['wall'] for r in rows if r['mode']==mode and r['route']==route and r['block']==block and r['arm']==arm) for arm in ['A','B']}
                relative=abs(medians['A']-medians['B'])/statistics.mean(medians.values())
                comparisons.append(dict(mode=mode,route=route,block=block,medians=medians,
                    relative_difference=relative,within_ten_percent=relative<=.10))
    result={'samples':rows,'preparation':preparation,'comparisons':comparisons,
        'stable_for_ten_percent_effect':all(c['within_ten_percent'] for c in comparisons),
        'limits':'Identical application both labels. New physical connection per measured request vs six warmups per label then four reads on verified same backend. No concurrent HTTP/Celery/dirty or load acceptance. Ten percent is pre-registered diagnostic threshold, not SLO; exceeding it is inconclusive method, not application FAIL.'}
    (out/'request-aa-results.json').write_text(json.dumps(result,indent=2)+'\n')
    record_property('request_aa_stability',json.dumps({'reads':len(rows),'stable':result['stable_for_ten_percent_effect']}))
