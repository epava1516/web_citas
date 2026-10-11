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


RECORD_DETAIL_TARGETS = {
    'validate_assessment': ('apps.safety.rights_portability_review', 'validate_approved_assessment'),
    'assessment_evidence': ('apps.safety.rights_portability', 'validate_assessment_evidence'),
    'selection_evidence': ('apps.safety.rights_portability_selection_store', 'validate_selection_evidence'),
    'audited_images': ('apps.safety.rights_portability_images', 'audited_images'),
    'checked_images': ('apps.safety.rights_portability_images', 'checked_images'),
    'read_image_blob': ('apps.safety.rights_exports', '_read_image_blob'),
    'content_digest': ('apps.safety.rights_operation_content_digests', 'content_digest'),
    'batch_projection': ('apps.safety.rights_portability_batch_projection', 'project'),
}


@pytest.mark.parametrize('phase', RECORD_DETAIL_TARGETS)
def test_record_detail_default_mapping_aliases_and_restore(modules, phase):
    owner_name, attribute = RECORD_DETAIL_TARGETS[phase]
    assert spans.PHASE_TARGETS[phase] == (owner_name, attribute)
    assert len(spans.PHASE_TARGETS) == 19
    assert len(spans.MODULES) == len(set(spans.MODULES))
    owner = sys.modules[owner_name]
    consumer = sys.modules['apps.safety.rights_portability_selection_review']
    result = object()

    def operation():
        return result

    setattr(owner, attribute, operation)
    consumer.detail_alias = operation
    with spans.scope(targets={phase: operation}) as collector:
        assert getattr(owner, attribute)() is result
        assert consumer.detail_alias() is result
    assert collector.snapshot()['phases'][phase]['calls'] == 2
    assert collector.snapshot()['status'] == 'complete'
    assert getattr(owner, attribute) is consumer.detail_alias is operation


def test_record_detail_missing_module_not_imported(modules, monkeypatch):
    missing = 'apps.safety.rights_portability_images'
    monkeypatch.delitem(sys.modules, missing)
    with spans.scope() as collector:
        assert missing not in sys.modules
    snapshot = collector.snapshot()
    assert {'audited_images', 'checked_images'} <= set(snapshot['missing_phases'])
    assert snapshot['incomplete']  # Required batch/page also absent in this fixture.
    assert missing not in sys.modules


def test_record_detail_nested_sql_innermost_exact_error_and_restore(modules):
    hooks = []
    error = ValueError('private physical-domain error')

    @contextmanager
    def provider(hook):
        hooks.append(hook)
        try:
            yield
        finally:
            hooks.pop()

    exports = sys.modules['apps.safety.rights_exports']
    reviewer = sys.modules['apps.safety.rights_portability_selection_review']

    def execute(sql, params, many, context):
        raise error

    def read_image():
        return hooks[-1](execute, 'private SQL', ['private parameter'], False, {})

    exports._read_image_blob = read_image

    def record():
        return exports._read_image_blob()

    reviewer.record = record
    with pytest.raises(ValueError) as captured:
        with spans.scope(targets={'record': record, 'read_image_blob': read_image},
                         sql_context=provider) as collector:
            reviewer.record()
    assert captured.value is error
    snapshot = collector.snapshot()
    assert snapshot['phases']['record']['calls'] == 1
    assert snapshot['phases']['read_image_blob']['calls'] == 1
    assert snapshot['phases']['record']['sql_count'] == 0
    assert snapshot['phases']['read_image_blob']['sql_count'] == 1
    assert 'private' not in str(snapshot)
    assert exports._read_image_blob is read_image
    assert reviewer.record is record
    assert not hooks


def test_detail_generator_is_omitted_without_wrapping_image_contents(modules):
    images = sys.modules['apps.safety.rights_portability_images']

    def image_contents():
        yield object()

    images.image_contents = image_contents
    images.audited_images = image_contents
    with spans.scope(targets={'audited_images': image_contents}) as collector:
        assert images.image_contents is image_contents
        assert images.audited_images is image_contents
    assert collector.snapshot()['omitted_phases'] == ['audited_images']
    assert collector.snapshot()['phases']['audited_images']['calls'] == 0


def test_exclusive_parent_minus_direct_children_no_double_count(modules, monkeypatch):
    wall = iter([0, 10, 20, 50, 60, 100])
    cpu = iter([0, 5, 10, 25, 30, 50])
    monkeypatch.setattr(spans, 'perf_counter_ns', lambda: next(wall))
    monkeypatch.setattr(spans, 'thread_time_ns', lambda: next(cpu))
    module = modules[0]

    def leaf():
        return 42

    module.leaf = leaf

    def record():
        return module.leaf()

    module.record = record

    def batch():
        return module.record()

    module.batch = batch
    with spans.scope(targets={'batch': batch, 'record': record, 'canonical_bytes': leaf}) as collector:
        assert module.batch() == 42
    phases = collector.snapshot()['phases']
    assert phases['batch']['wall_ns'] == 100
    assert phases['record']['wall_ns'] == 50
    assert phases['canonical_bytes']['wall_ns'] == 30
    assert [phases[name]['exclusive_wall_ns'] for name in ('batch', 'record', 'canonical_bytes')] == [50, 20, 30]
    assert sum(phases[name]['exclusive_thread_cpu_ns'] for name in ('batch', 'record', 'canonical_bytes')) == 50


def test_native_caller_wrappers_preserve_real_fallback_and_errors():
    import subprocess
    import textwrap

    script = textwrap.dedent('''
        import sys
        from apps.safety import fast_canonical
        from apps.safety.canonical_kernel_loader import validated_kernel
        from tests.capacity_phase_spans import scope
        assert validated_kernel() is not None
        original = fast_canonical.canonical_bytes
        nested = 0
        for _ in range(120):
            nested = [nested]
        def outcome(function, value):
            try:
                return ('ok', function(value))
            except Exception as error:
                return (type(error).__name__, str(error))
        for limit in (1000, 80):
            expected = []
            sys.setrecursionlimit(limit)
            for value in (None, {'a': (1, True)}, float('nan'), {1: 2}, nested):
                expected.append(outcome(original, value))
            sys.setrecursionlimit(1000)
            with scope(targets={'canonical_bytes': original}):
                sys.setrecursionlimit(limit)
                actual = [outcome(fast_canonical.canonical_bytes, value) for value in
                          (None, {'a': (1, True)}, float('nan'), {1: 2}, nested)]
                sys.setrecursionlimit(1000)
            assert expected == actual, (limit, expected, actual)
            assert fast_canonical.canonical_bytes is original
    ''')
    completed = subprocess.run([sys.executable, '-c', script], capture_output=True,
                               text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr


def test_negative_exclusive_marks_invalid_clock_not_silent_success(modules, monkeypatch):
    wall = iter([10, 0])
    monkeypatch.setattr(spans, 'perf_counter_ns', lambda: next(wall))
    def operation():
        return 42
    modules[0].record = operation
    with spans.scope(targets={'record': operation}) as collector:
        assert modules[0].record() == 42
    result = collector.snapshot()
    assert result['incomplete'] and result['reason'] == 'negative_duration'
    assert result['phases']['record']['exclusive_wall_ns'] == 0


def test_native_boundary_surveys_relevant_aliases_without_touching_kernel_identity(modules):
    native_module = sys.modules['apps.safety.fast_canonical']
    consumer = sys.modules['apps.safety.rights_inspection_source']
    rights = sys.modules['apps.safety.rights']
    copy_consumer = sys.modules['apps.safety.rights_copy_inspection']
    def canonical_bytes():
        return b'unchanged'
    def fingerprint():
        return 'unchanged'
    native_module.canonical_bytes = consumer.canonical_bytes = canonical_bytes
    rights.fingerprint = copy_consumer.fingerprint = fingerprint
    identity = object()
    native_module.kernel_identity = identity
    with spans.scope(targets={'canonical_bytes': canonical_bytes, 'fingerprint': fingerprint}) as collector:
        assert consumer.canonical_bytes() == b'unchanged'
        assert copy_consumer.fingerprint() == 'unchanged'
        assert native_module.kernel_identity is identity
    assert native_module.canonical_bytes is consumer.canonical_bytes is canonical_bytes
    assert rights.fingerprint is copy_consumer.fingerprint is fingerprint
    assert collector.snapshot()['phases']['canonical_bytes']['calls'] == 1
    assert collector.snapshot()['phases']['fingerprint']['calls'] == 1
