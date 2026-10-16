"""Attribute identical-code variability; diagnostic overhead is not acceptance."""
import gc
import json
import resource
import time
from pathlib import Path

import pytest
from django.db import connection
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_owned_request_aa_stability import test_owned_request_aa_stability as run_aa
from test_photos import photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_request_aa_attribution(request, monkeypatch):
    original = Client.get
    records = []
    def observed(client, path, *args, **kwargs):
        # The original A/A installs a SQL-count wrapper only for its measured reads.
        measured = bool(connection.execute_wrappers)
        if not measured:
            return original(client, path, *args, **kwargs)
        sql_wall = [0.0]
        intervals, active = [], {}
        def gc_event(phase, info):
            generation = info['generation']
            if phase == 'start':
                active[generation] = (time.perf_counter(), time.thread_time())
            elif generation in active:
                start, cpu = active.pop(generation)
                intervals.append({'generation':generation,'wall':time.perf_counter()-start,
                                  'cpu':time.thread_time()-cpu})
        def sql(execute, query, params, many, context):
            start = time.perf_counter()
            try:
                return execute(query, params, many, context)
            finally:
                sql_wall[0] += time.perf_counter()-start
        before = resource.getrusage(resource.RUSAGE_THREAD)
        gc.callbacks.append(gc_event)
        start, cpu = time.perf_counter(), time.thread_time()
        try:
            with connection.execute_wrapper(sql):
                return original(client, path, *args, **kwargs)
        finally:
            wall, used = time.perf_counter()-start, time.thread_time()-cpu
            gc.callbacks.remove(gc_event)
            after = resource.getrusage(resource.RUSAGE_THREAD)
            records.append({'path':path,'wall':wall,'cpu':used,'sql_wall_inclusive':sql_wall[0],
                'gc':intervals,'unfinished_gc':len(active),
                'voluntary_switches':after.ru_nvcsw-before.ru_nvcsw,
                'involuntary_switches':after.ru_nivcsw-before.ru_nivcsw})
    monkeypatch.setattr(Client, 'get', observed)
    # Preserve the explicit opt-in guard of the shared A/A test without copying it.
    original_args = request.config.args
    request.config.args = ['tests/test_owned_request_aa_stability.py']
    try:
        run_aa(request, lambda *args: None)
    finally:
        request.config.args = original_args
        out = Path(request.config.getoption('--gate-timings-output')).parent
        (out/'request-aa-attribution.json').write_text(json.dumps(records,indent=2)+'\n')
    assert len(records) == 96 and all(not row['unfinished_gc'] for row in records)
