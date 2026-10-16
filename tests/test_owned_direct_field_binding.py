"""Finite read-only-snapshot direct scalar field binding experiment, no product change."""
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


def test_owned_direct_field_binding(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_direct_field_binding.py' for x in request.config.args):
        pytest.skip('Explicit finite direct field binding experiment only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    client = request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    original = public_validation.validate_publication_binding
    source = textwrap.dedent(inspect.getsource(original))
    needle = '    uses_value_kernel = False\n'
    assert source.count(needle) == 1
    source = source.replace(needle, """    if (not value_model and type(form) in (SnapshotDetails, ContactsForm)
            and not needs_initial and all(name in data for name in form.fields)
            and form.bound_field_class in (None, forms.BoundField)
            and all(field.bound_field_class in (None, forms.BoundField) for field in form.fields.values())):
        _owned_fast_bindings[0] += 1
        form._clean_fields = lambda: validate_publication_input_fields(form)
    uses_value_kernel = False
""")
    source = source.replace('        form._bound_fields_cache.clear()\n',
        '        form._bound_fields_cache.clear()\n        form.__dict__.pop("_clean_fields", None)\n')
    namespace = vars(public_validation).copy()
    counter = [0]
    namespace['_owned_fast_bindings'] = counter
    exec(compile(source, '<owned-direct-field-binding>', 'exec'), namespace)
    proposed = namespace['validate_publication_binding']
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
                arms = [('current', original), ('direct_fields', proposed)]
                if block % 2:
                    arms.reverse()
                for arm, implementation in arms:
                    connection.close()
                    with monkeypatch.context() as patch:
                        patch.setattr(public_validation, 'validate_publication_binding', implementation)
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
            assert signatures['current'] == signatures['direct_fields']
    assert counter[0] > 0, 'Candidate path was not exercised'
    record_property('direct_field_bindings', counter[0])
    (out/'direct-field-binding-results.json').write_text(json.dumps(records, indent=2)+'\n')
    record_property('direct_field_binding_results', json.dumps(records))
    record_property('limits', '48 anonymous actual Django Client list/search ESEN reads, own10k PG, clean/dirty1, three ABBA blocks. Same bytes/status/no-store. SQL counts only, no profiler/Celery/sockets/p95. Experimental validate_publication_binding overrides only scalar _clean_fields for complete audited bindings, leaves native _post_clean/full model validation. Counter proves use. Custom field hooks, mutations, invalid inputs, errors and exceptional cleanup require N2 before product; no application source change.')
