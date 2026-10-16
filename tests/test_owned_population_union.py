"""Finite real-reader contrast: complete state coverage with a small dirty set."""
import inspect
import json
import os
import time
from pathlib import Path

import pytest
from django.conf import settings
from django.db import connection
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.discovery import candidates
from apps.listings.models import Listing
from apps.safety.canonical_kernel_loader import kernel_identity
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_population_union(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_population_union.py' for x in request.config.args):
        pytest.skip('Explicit owned finite comparison only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    assert kernel_identity()['mode'] == 'native-sealed'
    request.getfixturevalue('directory')
    monkeypatch.setattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    populate(10000)
    publication_state.refresh_all()
    native = publication_state._state_page
    source = inspect.getsource(native)
    needle = '    population = population_query.select_related(None).filter(trusted_visible | Q(pk__in=native))'
    assert source.count(needle) == 1
    source = source.replace(needle, """    if trusted_snapshot and dirty:
        trusted_ids = eligible_ids.exclude(listing_id__in=dirty).order_by()
        native_ids = Listing.objects.filter(pk__in=native).order_by().values_list('pk', flat=True)
        population = population_query.select_related(None).filter(pk__in=trusted_ids.union(native_ids))
    else:
        population = population_query.select_related(None).filter(trusted_visible | Q(pk__in=native))""")
    namespace = vars(publication_state).copy()
    exec(compile(source, '<owned-population-union-candidate>', 'exec'), namespace)
    proposed = namespace['_state_page']
    records = []
    for dirty in (False, True):
        if dirty:
            publication_state.mark([Listing.objects.filter(status='published').first().pk])
        for text in ('', 'photography', 'zzznomatchproof'):
            for block in range(3):
                arms = [('native', native), ('union', proposed)]
                if block % 2:
                    arms.reverse()
                signatures = {}
                for arm, implementation in arms:
                    connection.close()
                    with monkeypatch.context() as patch:
                        patch.setattr(publication_state, '_state_page', implementation)
                        for repeat in range(3):
                            start, cpu = time.perf_counter(), time.thread_time()
                            page = publication_state.state_page(candidates({'q':text}), 1)
                            assert page is not None
                            signature = (page.paginator.count, tuple(str(r.pk) for r in page))
                            records.append({'dirty':dirty,'text':text,'block':block,'arm':arm,'repeat':repeat,
                                            'wall_s':time.perf_counter()-start,'cpu_s':time.thread_time()-cpu})
                            signatures.setdefault(arm,signature)
                            assert signatures[arm] == signature
                assert signatures['native'] == signatures['union']
    record_property('population_union',json.dumps(records))
    record_property('limits','Full synthetic10k sequential state_page only; no HTTP/p95 claim. Candidate changes only outer RR dirty population membership; projection remains disabled. Missing/outdated state and inherited transactions need separate parity controls before adoption.')
