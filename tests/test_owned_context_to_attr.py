"""Bounded to_attr hydration contrast; application source remains unchanged."""
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


def test_owned_context_to_attr(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_context_to_attr.py' for x in request.config.args):
        pytest.skip('Explicit finite hydration contrast only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    original = public_validation.PublicationContext.__init__
    source = textwrap.dedent(inspect.getsource(original))
    needle = 'query = query.prefetch_related(Prefetch("approved_revision__" + name))'
    assert source.count(needle) == 1
    source = source.replace(needle, 'query = query.prefetch_related(Prefetch("approved_revision__" + name, to_attr="_pv_" + name))')
    needle = '        for relation in ["categories", "services", "travel_areas", "rates"]:\n            setattr(revision, "_pv_" + relation, list(getattr(revision, relation).all()))\n'
    assert source.count(needle) == 1
    source = source.replace(needle, '')
    namespace = vars(public_validation).copy()
    exec(compile(source, '<owned-context-to-attr>', 'exec'), namespace)
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
                arms = [('current', original), ('to_attr', proposed)]
                if block % 2:
                    arms.reverse()
                for arm, implementation in arms:
                    connection.close()
                    with monkeypatch.context() as patch:
                        patch.setattr(public_validation.PublicationContext, '__init__', implementation)
                        for repeat in range(3):
                            wall, cpu = time.perf_counter(), time.thread_time()
                            response = client.get(route)
                            elapsed, used = time.perf_counter()-wall, time.thread_time()-cpu
                            assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                            digest = hashlib.sha256(response.content).hexdigest()
                            expected = signatures.setdefault(arm, digest)
                            assert expected == digest
                            records.append({'dirty':dirty, 'case':case, 'block':block, 'arm':arm,
                                            'repeat':repeat, 'wall_s':elapsed, 'cpu_s':used})
                assert signatures['current'] == signatures['to_attr']
    record_property('context_to_attr', json.dumps(records))
    record_property('limits', '72 sequential actual Django client reads, own10k PG, clean and one dirty listing, three AB/BA blocks. Same response bytes/status/no-store. Four relations only, instance-owned lists; no shared authorization cache. Not all concurrency/filters/ordering/negative cases; no sockets/admission/Celery/p95 or causal load acceptance.')
