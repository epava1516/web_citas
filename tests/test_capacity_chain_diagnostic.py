"""Observer forwarding/error restoration; these are not DB integration claims."""
from types import SimpleNamespace

import pytest

from tests.capacity_chain_diagnostic import Collector, Cursor, observed


def test_cursor_forwards_and_reports_only_numeric_event_rows():
    class Original:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

        def execute(self, query, params):
            assert params == ['synthetic']

        def fetchall(self):
            return [(1, 'private-digest'), (2, 'private-digest')]

    collector, original = Collector(), Original()
    with Cursor(original, collector) as cursor:
        cursor.execute('SELECT rights_evidence_link(request_id)', ['synthetic'])
        assert cursor.fetchall() == [(1, 'private-digest'), (2, 'private-digest')]
    assert original.closed
    assert collector.event_rows == [2]
    assert 'private-digest' not in str(collector.snapshot())


def test_observer_scope_restores_aliases_and_pipeline_after_failure():
    from psycopg import Pipeline

    from apps.safety import evidence_chain
    from tests.capacity_chain_diagnostic import scope

    original, sync = evidence_chain.validate_chain, Pipeline.sync
    with pytest.raises(RuntimeError, match='synthetic'):
        with scope() as collector:
            assert evidence_chain.validate_chain is not original
            with collector.span('probe'):
                raise RuntimeError('synthetic')
    assert evidence_chain.validate_chain is original and Pipeline.sync is sync
    assert not collector.stack


def test_wrapper_preserves_return_and_exception_without_scope():
    result = SimpleNamespace(count=3)
    assert observed(lambda: result, 'chain')() is result

    def failure():
        raise ValueError('synthetic')

    with pytest.raises(ValueError, match='synthetic'):
        observed(failure, 'chain')()
