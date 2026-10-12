"""Diagnostic forwarding and restoration, not simulated database evidence."""
import pytest

from tests.capacity_wait_diagnostic import _active, measured, scope


def test_preserves_return_and_exception_without_scope():
    value = object()
    assert measured(lambda: value, 'execute')() is value
    def fail():
        raise ValueError('probe')
    with pytest.raises(ValueError, match='probe'):
        measured(fail, 'execute')()


def test_scope_restores_driver_pipeline_and_phase_after_exception():
    import psycopg

    from apps.listings.models import Revision
    from apps.safety import rights_exports
    original, execute, sync = rights_exports.source_copy, psycopg.Cursor.execute, psycopg.Pipeline.sync
    hydration = Revision.from_db.__func__
    server_execute, server_fetch = psycopg.ServerCursor.execute, psycopg.ServerCursor.fetchmany
    with pytest.raises(ValueError, match='probe'):
        with scope() as collector:
            def fail():
                raise ValueError('probe')
            measured(fail, 'source', phase=True)()
    assert Revision.from_db.__func__ is hydration
    assert not collector.stack and _active.get() is None
    assert rights_exports.source_copy is original
    assert psycopg.Cursor.execute is execute and psycopg.Pipeline.sync is sync
    assert psycopg.ServerCursor.execute is server_execute and psycopg.ServerCursor.fetchmany is server_fetch


def test_records_only_counts_and_exclusive_nested_spans():
    with scope() as collector:
        fetch = measured(lambda: [('synthetic-private-payload',)], 'driver_fetchall', fetch=True)
        assert measured(fetch, 'source', phase=True)() == [('synthetic-private-payload',)]
    assert collector.fetch_counts == {'source.driver_fetchall': [1]}
    assert 'synthetic-private-payload' not in str(collector.snapshot())
    outer, inner = collector.spans['source'], collector.spans['source.driver_fetchall']
    assert outer['exclusive_wall_ns'] == outer['wall_ns'] - inner['wall_ns']
