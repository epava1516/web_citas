"""Observer cleanup/forwarding, not DB or HTTP verification."""
from contextlib import contextmanager

import pytest

from tests.capacity_chain_diagnostic import Collector
from tests.capacity_source_diagnostic import context_observed, iterated, scope


def test_iteration_only_advances_under_span_and_closes():
    closed = []
    def generator():
        try:
            yield 1
            yield 2
        finally:
            closed.append(True)
    collector = Collector()
    iterator = iterated(generator, collector)()
    assert next(iterator) == 1 and not collector.stack
    assert next(iterator) == 2 and not collector.stack
    with pytest.raises(StopIteration):
        next(iterator)
    assert collector.spans['batches_active_next']['calls'] == 3 and closed == [True]


@pytest.mark.parametrize('suppress', [False, True])
def test_context_exception_semantics(suppress):
    @contextmanager
    def original():
        try:
            yield 'synthetic'
        except ValueError:
            if not suppress:
                raise
    collector = Collector()
    def operation():
        with context_observed(original, collector)() as value:
            assert value == 'synthetic' and not collector.stack
            raise ValueError('synthetic')
    if suppress:
        operation()
    else:
        with pytest.raises(ValueError):
            operation()
    assert not collector.stack
    assert collector.spans['source_context_exit']['calls'] == 1


def test_scope_restores_after_exception():
    from django.db.models.query import QuerySet

    from apps.safety import rights_exports, rights_inspection_source
    original = rights_exports.source_copy
    context = rights_inspection_source.inspection_source
    fetch = QuerySet._fetch_all
    with pytest.raises(ValueError):
        with scope() as collector:
            assert rights_exports.source_copy is not original
            raise ValueError('synthetic')
    assert rights_exports.source_copy is original
    assert rights_inspection_source.inspection_source is context
    assert QuerySet._fetch_all is fetch
    assert not collector.stack and collector.cpu_profile
