"""Finite read-only-snapshot geographic catalog reuse experiment, no product change."""
import hashlib
import inspect
import json
import os
import textwrap
import time
from pathlib import Path

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation, publication_state
from apps.listings.models import Listing
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_geo_catalog_reuse(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_geo_catalog_reuse.py' for x in request.config.args):
        pytest.skip('Explicit finite geographic catalog experiment only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    original = public_validation.PublicationContext.__init__
    source = textwrap.dedent(inspect.getsource(original))
    needle = '    for name, values in ids.items():\n'
    assert source.count(needle) == 1
    source = source.replace(needle, '''    geo = {name: {} for name in ['municipality', 'province', 'region']}
    if prepared_page:
        for row in self.rows:
            revision = row.approved_revision
            if revision and revision.municipality_id:
                city = revision.municipality
                if city.active:
                    geo['municipality'][str(city.pk)] = city
                geo['province'][str(city.province_id)] = city.province
                geo['region'][str(city.province.region_id)] = city.province.region
    for name, values in ids.items():
        if prepared_page and name in geo:
            self.catalog[name] = {str(pk): geo[name][str(pk)] for pk in values if str(pk) in geo[name]}
            continue
''')
    namespace = vars(public_validation).copy()
    exec(compile(source, '<owned-geographic-catalog>', 'exec'), namespace)
    proposed = namespace['__init__']
    routes = ['/es/', '/en/?q=synthetic']
    for route in routes:
        assert client.get(route).status_code == 200
    records = []
    for dirty in (False, True):
        if dirty:
            publication_state.mark([Listing.objects.filter(status='published').first().pk])
        for case, route in enumerate(routes):
            signatures = {}
            for block in range(3):
                arms = [('current', original), ('geo_reuse', proposed)]
                if block % 2:
                    arms.reverse()
                for arm, implementation in arms:
                    connection.close()
                    with monkeypatch.context() as patch:
                        patch.setattr(public_validation.PublicationContext, '__init__', implementation)
                        for repeat in range(2):
                            calls = [0]
                            def counted(execute, sql, params, many, context):
                                calls[0] += 1
                                return execute(sql, params, many, context)
                            wall, cpu = time.perf_counter(), time.thread_time()
                            with connection.execute_wrapper(counted):
                                response = client.get(route)
                            elapsed, used = time.perf_counter()-wall, time.thread_time()-cpu
                            assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                            digest = hashlib.sha256(response.content).hexdigest()
                            signatures.setdefault(arm, digest)
                            assert signatures[arm] == digest
                            records.append(dict(dirty=dirty, case=case, block=block, arm=arm,
                                                repeat=repeat, wall=elapsed, cpu=used, sql=calls[0]))
            assert signatures['current'] == signatures['geo_reuse']
    (out/'geo-catalog-results.json').write_text(json.dumps(records, indent=2)+'\n')
    record_property('geo_catalog_results', json.dumps(records))
    record_property('limits', '48 sequential anonymous Django Client list/search ES/EN reads, 3 AB/BA blocks, own10k PG, clean/dirty1. Same bytes/status/no-store; SQL count without texts or params. Experimental constructor only; uses captured city/province/region in state-page prepared context under owned RR snapshot. Unknown customized querysets, inherited RC, wider geographic fixtures, revocation/concurrency and product API gating not proven; no shared data cache, sockets/Celery/profilers/p95/load acceptance.')
