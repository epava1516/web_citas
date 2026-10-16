"""Bounded attribution of duplicate request-local publication catalog reads."""
import hashlib
import json
import os
import re
import time
from pathlib import Path

import pytest
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation, publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_context_duplicate_reads(request, monkeypatch):
    if not any(str(x).split('::')[0] == 'tests/test_owned_context_duplicate_reads.py'
               for x in request.config.args):
        pytest.skip('Explicit own-context duplicate-read diagnosis only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    request.getfixturevalue('directory')
    dataset = populate(10000)
    target = Listing.objects.select_related('approved_revision').get(pk=dataset['sample_ids'][0])
    Revision.objects.create(listing=target, manager_version=target.approved_revision.manager_version)
    publication_state.refresh_all()
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    original = public_validation.PublicationContext.__init__
    records, active = [], []

    def observed_init(context, *args, **kwargs):
        row = dict(stage='page' if kwargs.get('prepared_page') else 'unknown',
                   sql=0, catalog_sql=0, sql_wall=0., catalog_sql_wall=0.)
        active.append(row)
        wall, cpu = time.perf_counter(), time.thread_time()
        try:
            original(context, *args, **kwargs)
        finally:
            row.update(wall=time.perf_counter() - wall, cpu=time.thread_time() - cpu)
            active.pop()
        row['rows'] = len(context.rows)
        row['catalog_keys'] = {name: frozenset(values) for name, values in context.catalog.items()}
        records.append(row)

    monkeypatch.setattr(public_validation.PublicationContext, '__init__', observed_init)
    handler, factory = WSGIHandler(), RequestFactory()

    def call(route):
        status = []

        def start_response(value, headers, exc_info=None):
            status.append((value, dict(headers)))

        response = handler(factory.get(route).environ, start_response)
        try:
            body = b''.join(response)
        finally:
            response.close()
        assert status[0][0].startswith('200 ') and status[0][1]['Cache-Control'] == 'no-store'
        return hashlib.sha256(body).hexdigest()

    def observed_sql(execute, sql, params, many, context):
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            if active:
                row = active[-1]
                row['sql'] += 1
                elapsed = time.perf_counter() - started
                row['sql_wall'] += elapsed
                if '"_pv_history"' not in sql and re.search(r'FROM "catalog_[a-z_]+"', sql):
                    row['catalog_sql'] += 1
                    row['catalog_sql_wall'] += elapsed

    output, signatures = [], {}
    for mode in ['clean', 'dirty1']:
        if mode == 'dirty1':
            publication_state.mark([target.pk])
        marks = list(PublicationDirty.objects.values_list('pk', 'generation'))
        for route in ['/es/', '/en/?q=synthetic']:
            connection.close()
            for _ in range(6):
                signature = call(route)
                signatures.setdefault(route, signature)
                assert signature == signatures[route]
            for repeat in range(3):
                records.clear()
                with connection.execute_wrapper(observed_sql):
                    assert call(route) == signatures[route]
                assert not active
                assert [row['rows'] for row in records] == ([24] if mode == 'clean' else [1, 24])
                overlap = None
                if mode == 'dirty1':
                    first, second = [row['catalog_keys'] for row in records]
                    overlap = {name: {'unknown': len(first[name]), 'page': len(second[name]),
                                      'shared': len(first[name] & second[name]),
                                      'exact_keys': first[name] == second[name]} for name in first}
                for row in records:
                    row['catalog_sizes'] = {name: len(values) for name, values in row.pop('catalog_keys').items()}
                output.append(dict(mode=mode, route=route, repeat=repeat,
                                   contexts=list(records), catalog_overlap=overlap))
        assert list(PublicationDirty.objects.values_list('pk', 'generation')) == marks
    assert len(output) == 12
    (out / 'context-duplicate-reads.json').write_text(json.dumps({
        'samples': output,
        'limits': 'Diagnostic wrappers, normal GC, 12 sequential real WSGI reads after warmup, '
                  'no Client/template capture. Context wall/CPU includes SQL and overhead; phases '
                  'overlap and do not prove causal savings. Catalog keys compared only in memory, '
                  'only cardinalities/equality exported. No product change, cache reuse or SLO.',
    }, indent=2) + '\n')
