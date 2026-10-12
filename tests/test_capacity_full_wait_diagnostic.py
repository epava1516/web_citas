"""Forwarding and restoration of test-only adaptation instrumentation."""
from types import SimpleNamespace

import pytest

from tests.capacity_full_wait_diagnostic import AdaptationProxy, adapted_fetch, scope
from tests.capacity_wait_diagnostic import _active


def test_proxy_preserves_adaptation_result_and_restores_on_throw():
    value = [("private-synthetic-value",)]
    transformer = SimpleNamespace(load_rows=lambda *a, **kw: value, set_pgresult=lambda *a, **kw: None)
    cursor = SimpleNamespace(_tx=transformer)
    def fetch(cursor):
        yield 1
        cursor._tx.set_pgresult(None)
        return cursor._tx.load_rows(0, 1, None)
    with scope() as collector:
        generator = adapted_fetch(fetch)(cursor)
        assert next(generator) == 1 and isinstance(cursor._tx, AdaptationProxy)
        with pytest.raises(StopIteration) as stopped:
            next(generator)
        assert stopped.value.value is value and cursor._tx is transformer
        assert 'private-synthetic-value' not in str(collector.snapshot())
        generator = adapted_fetch(fetch)(cursor)
        next(generator)
        with pytest.raises(ValueError):
            generator.throw(ValueError('probe'))
        assert cursor._tx is transformer
    assert _active.get() is None


def test_scope_restores_full_phases_and_driver_generator_on_exception():
    import psycopg

    from apps.safety import rights_portability_coverage_batch
    original = rights_portability_coverage_batch.inspect_batch
    original_fetch = psycopg.ServerCursor._fetch_gen
    with pytest.raises(ValueError):
        with scope():
            assert original is not rights_portability_coverage_batch.inspect_batch
            raise ValueError('probe')
    assert rights_portability_coverage_batch.inspect_batch is original
    assert psycopg.ServerCursor._fetch_gen is original_fetch
