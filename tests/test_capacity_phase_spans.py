"""Dependency-free observer tests; these are not application acceptance."""
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from types import ModuleType

import pytest

from tests import capacity_phase_spans as spans


@pytest.fixture
def modules(monkeypatch):
    result = []
    for name in spans.MODULES:
        module = ModuleType(name)
        monkeypatch.setitem(sys.modules, name, module)
        result.append(module)
    return result


def test_four_sequential_pages_one_batch_aliases_and_results(modules):
    order = []
    source_module, caller_module = modules[:2]

    def page(value):
        order.append(value)
        return {'value': value}

    source_module.inspect_page = page
    caller_module.alias = page

    def batch():
        return [caller_module.alias(index) for index in range(4)]

    source_module.inspect_batch = batch
    with spans.scope(targets={'batch': batch, 'page': page}) as collector:
        result = source_module.inspect_batch()
    snapshot = collector.snapshot()
    assert result == [{'value': index} for index in range(4)]
    assert order == list(range(4))
    assert snapshot['phases']['batch']['calls'] == 1
    assert snapshot['phases']['page']['calls'] == 4
    assert len(snapshot['pages']) == 4
    assert all(item['page']['calls'] == 1 for item in snapshot['pages'])
    assert snapshot['status'] == 'complete'
    assert caller_module.alias is source_module.inspect_page is page
    snapshot['phases']['page']['calls'] = -1
    assert collector.snapshot()['phases']['page']['calls'] == 4


def test_sql_counts_wall_cpu_innermost_no_text_and_domain_exception(modules):
    hooks = []

    @contextmanager
    def sql_context(hook):
        hooks.append(hook)
        try:
            yield
        finally:
            hooks.pop()

    error = RuntimeError('private domain message')

    def execute(sql, params, many, context):
        assert sql == 'SECRET SQL' and params == ['SECRET PARAM']
        raise error

    def record():
        return hooks[-1](execute, 'SECRET SQL', ['SECRET PARAM'], False, {})

    modules[0].record = record
    with pytest.raises(RuntimeError) as captured:
        with spans.scope(targets={'record': record}, sql_context=sql_context) as collector:
            modules[0].record()
    assert captured.value is error
    assert not hooks
    snapshot = collector.snapshot()
    assert snapshot['phases']['record']['sql_count'] == 1
    assert snapshot['phases']['record']['sql_wall_ns'] >= 0
    assert snapshot['phases']['record']['sql_thread_cpu_ns'] >= 0
    assert 'SECRET' not in str(snapshot)
    assert 'private domain' not in str(snapshot)
    assert modules[0].record is record


def test_nested_and_concurrent_scope_decline_unmarked_threads_bypass(modules):
    def page():
        return 7

    modules[0].page = page
    with spans.scope(targets={'page': page}) as outer:
        with spans.scope(targets={'page': page}) as nested:
            assert nested.snapshot()['status'] == 'declined'
        def thread():
            with spans.scope(targets={'page': page}) as concurrent:
                return concurrent.snapshot()['status'], modules[0].page()
        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(thread).result(timeout=5) == ('declined', 7)
        assert modules[0].page() == 7
    assert outer.snapshot()['phases']['page']['calls'] == 1


def test_foreign_replacement_preserved_and_context_reset(modules):
    def original():
        return 1
    def foreign():
        return 2
    modules[0].record = original
    with spans.scope(targets={'record': original}) as collector:
        modules[0].record = foreign
    assert modules[0].record is foreign
    assert collector.snapshot()['reason'] == 'foreign_replacement'
    assert spans._current.get() is None


def test_observer_clock_failure_does_not_replace_domain_exception(modules, monkeypatch):
    error = ValueError('domain')
    def original():
        raise error
    modules[0].record = original
    monkeypatch.setattr(spans, 'perf_counter_ns', lambda: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(ValueError) as captured:
        with spans.scope(targets={'record': original}) as collector:
            modules[0].record()
    assert captured.value is error
    assert collector.snapshot()['incomplete']
    assert modules[0].record is original


def test_generator_contextmanager_and_coroutine_omitted(modules):
    def generator():
        yield 1
    @contextmanager
    def context():
        yield 2
    async def coroutine():
        return 3
    modules[0].source = generator
    modules[0].record = context
    modules[0].page = coroutine
    with spans.scope(targets={'source': generator, 'record': context, 'page': coroutine}) as collector:
        assert modules[0].source is generator
        assert modules[0].record is context
        assert modules[0].page is coroutine
    assert set(collector.snapshot()['omitted_phases']) == {'source', 'record', 'page'}


@pytest.mark.parametrize('bound', ['MAX_CALLS', 'MAX_DEPTH', 'MAX_ALIASES'])
def test_finite_bounds_preserve_call_results(modules, monkeypatch, bound):
    monkeypatch.setattr(spans, bound, 0)
    def original():
        return 99
    modules[0].record = original
    with spans.scope(targets={'record': original}) as collector:
        assert modules[0].record() == 99
    assert collector.snapshot()['incomplete']
    assert modules[0].record is original


def test_fifth_page_does_not_grow_metrics(modules):
    def original():
        return 1
    modules[0].page = original
    with spans.scope(targets={'page': original}) as collector:
        assert [modules[0].page() for _ in range(5)] == [1] * 5
    assert len(collector.snapshot()['pages']) == 4
    assert collector.snapshot()['reason'] == 'page_bound_or_overlap'


def test_disabled_no_install_or_sql_provider(modules):
    def original():
        return 1
    modules[0].record = original
    def forbidden(hook):
        pytest.fail('provider called')
    with spans.scope(enabled=False, targets={'record': original}, sql_context=forbidden) as collector:
        assert modules[0].record is original
    assert collector.snapshot()['status'] == 'inactive'


def test_sql_restore_failure_preserves_domain_exception(modules):
    error = ValueError('original domain')
    @contextmanager
    def sql_context(hook):
        try:
            yield
        finally:
            raise RuntimeError('observer teardown')
    with pytest.raises(ValueError) as captured:
        with spans.scope(targets={}, sql_context=sql_context) as collector:
            raise error
    assert captured.value is error
    assert collector.snapshot()['reason'] == 'sql_restore_failure'
    assert spans._current.get() is None


def test_sql_bound_preserves_calls_and_global_totals(monkeypatch):
    monkeypatch.setattr(spans, 'MAX_SQL', 1)
    holder = []
    @contextmanager
    def provider(hook):
        holder.append(hook)
        yield
    def execute(sql, params, many, context):
        return 42
    with spans.scope(targets={}, sql_context=provider) as collector:
        assert holder[0](execute, 'unused', None, False, {}) == 42
        assert holder[0](execute, 'unused', None, False, {}) == 42
    assert collector.snapshot()['sql_count'] == 1
    assert collector.snapshot()['reason'] == 'sql_bound'
    assert collector.snapshot()['sql_totals']['wall_ns'] >= 0


def test_time_bound_clamps_metrics_and_next_scope_is_fresh(modules, monkeypatch):
    clock = iter([0, spans.MAX_NS + 1])
    monkeypatch.setattr(spans, 'perf_counter_ns', lambda: next(clock))
    def original():
        return 42
    modules[0].record = original
    with spans.scope(targets={'record': original}) as collector:
        assert modules[0].record() == 42
    assert collector.snapshot()['reason'] == 'time_bound'
    assert collector.snapshot()['phases']['record']['wall_ns'] == spans.MAX_NS
    with spans.scope(targets={}) as next_collector:
        assert next_collector.snapshot()['phases']['record']['calls'] == 0
    assert next_collector.snapshot()['status'] == 'complete'


def test_default_missing_modules_report_missing_required_phases(modules):
    with spans.scope() as collector:
        result = 42
    assert result == 42
    snapshot = collector.snapshot()
    assert snapshot['incomplete']
    assert snapshot['reason'] == 'missing_required_target'
    assert set(snapshot['missing_phases']) == set(spans.PHASE_TARGETS)


def test_supplied_orphan_callable_incomplete_even_if_domain_succeeds(modules):
    def orphan():
        return 42
    with spans.scope(targets={'record': orphan}) as collector:
        assert orphan() == 42
    assert collector.snapshot()['reason'] == 'missing_alias'
    assert collector.snapshot()['missing_phases'] == ['record']
    assert collector.snapshot()['status'] == 'incomplete'


def test_partial_sql_provider_entry_cleans_up_without_masking_domain(modules):
    installed = []
    exits = []
    domain = ValueError('exact domain exception')

    class PartialProvider:
        def __enter__(self):
            installed.append(True)
            raise RuntimeError('observer entry failure')

        def __exit__(self, kind, value, traceback):
            installed.clear()
            exits.append(value)
            return True  # Diagnostic provider cannot suppress the domain.

    with pytest.raises(ValueError) as captured:
        with spans.scope(targets={}, sql_context=lambda hook: PartialProvider()) as collector:
            raise domain
    assert captured.value is domain
    assert not installed
    assert exits == [domain]
    assert collector.snapshot()['reason'] == 'installation_failure'
    assert spans._current.get() is None
