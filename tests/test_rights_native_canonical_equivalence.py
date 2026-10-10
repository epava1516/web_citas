"""Differential semantics; native cases require the verified loader's actual kernel."""
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import IntEnum
from types import ModuleType
from uuid import UUID

import orjson
import pytest

from apps.safety import fast_canonical as canonical


@pytest.fixture
def native_check():
    try:
        from apps.safety.canonical_kernel_loader import validated_kernel
    except ModuleNotFoundError as error:
        if error.name != 'apps.safety.canonical_kernel_loader':
            raise
        pytest.skip('Native equivalence pending verified build/loader; fallback is not native evidence')
    kernel = validated_kernel()
    if kernel is None:
        pytest.skip('Native equivalence requires an available verified kernel')
    return kernel


def result(check, value, depth=0, *, encode=False):
    try:
        check(value, depth)
        return ('bytes', orjson.dumps(value, option=orjson.OPT_SORT_KEYS)) if encode else ('accepted',)
    except Exception as error:
        return ('rejected', type(error), str(error))


@pytest.mark.parametrize('value', [None, True, False, 0, -1, -(2 ** 63), 2 ** 64 - 1,
    -(2 ** 63) - 1, 2 ** 64, 2 ** 10000, 0.0, -0.0, 5e-324, 1.7976931348623157e308,
    '', 'á', 'a\u0301', '😀', '\ud800', '\udfff', '\ud800\udfff', [], (), {},
    {'z': [True, 1, {'nested': ('text', None)}], 'a': 0}], ids=[
    'none', 'true', 'false', 'zero', 'negative', 'minint', 'maxint', 'belowmin',
    'abovemax', 'hugeint', 'floatzero', 'negzero', 'subnormal', 'maxfloat', 'emptystr',
    'unicode', 'combining', 'emoji', 'highsurrogate', 'lowsurrogate', 'surrogatepair',
    'list', 'tuple', 'dict', 'nested'])
def test_native_matches_validation_and_encoder_stage_exactly(native_check, value):
    assert result(native_check, value) == result(canonical.reference_check, value)
    assert result(native_check, value, encode=True) == result(canonical.reference_check, value, encode=True)


@dataclass
class Data:
    value: int = 1


class Number(IntEnum):
    value = 1


class Str(str):
    pass


class Int(int):
    pass


class Float(float):
    pass


class Dict(dict):
    pass


class List(list):
    pass


class Tuple(tuple):
    pass


@pytest.mark.parametrize('factory', [lambda: math.nan, lambda: math.inf, lambda: -math.inf,
    lambda: {1: 'bad'}, lambda: {Str('key'): 1}, lambda: Str('value'), lambda: Int(1),
    lambda: Float(1), lambda: Dict(a=1), lambda: List([1]), lambda: Tuple([1]),
    lambda: Number.value, lambda: Decimal('1.2'), lambda: UUID(int=1),
    lambda: datetime(2020, 1, 1, tzinfo=timezone.utc), Data, lambda: set([1]),
    lambda: iter([1]), lambda: {'a': [0, math.nan]}, lambda: {'a': [1], 0: None}],
    ids=['nan', 'inf', 'neginf', 'intkey', 'strsubkey', 'strsub', 'intsub', 'floatsub',
         'dictsub', 'listsub', 'tuplesub', 'enum', 'decimal', 'uuid', 'datetime',
         'dataclass', 'set', 'iterator', 'nestednan', 'latekey'])
def test_native_rejected_values_keep_exception_class_message_and_order(native_check, factory):
    value = factory()
    expected = result(canonical.reference_check, value)
    assert expected[0] == 'rejected'
    assert result(native_check, value) == expected


def nested(depth):
    value = 0
    for _ in range(depth):
        value = [value]
    return value


@pytest.mark.parametrize('depth', [199, 200, 201])
def test_native_depth_check_precedes_terminal_leaf(native_check, depth):
    value = nested(depth)
    assert result(native_check, value) == result(canonical.reference_check, value)


@pytest.mark.parametrize('mutual', [False, True])
def test_native_cycles_stop_at_depth_201_without_crash(native_check, mutual):
    value = []
    if mutual:
        peer = {'cycle': value}
        value.append(peer)
    else:
        value.append(value)
    assert result(native_check, value) == result(canonical.reference_check, value)


@pytest.mark.parametrize('depth', [True, 1.5, -1, 201, 2 ** 10000])
def test_native_public_depth_keeps_reference_behavior(native_check, depth):
    assert result(native_check, [0], depth) == result(canonical.reference_check, [0], depth)


def test_native_revalidates_mutable_inputs_every_call_and_never_coerces(native_check):
    value = {'a': [True, 1], 'z': 'original'}
    before = orjson.dumps(value)
    native_check(value)
    assert orjson.dumps(value) == before and type(value['a'][0]) is bool
    value['a'].append(math.nan)
    assert result(native_check, value) == result(canonical.reference_check, value)
    value['a'].pop()
    value[1] = 'invalid key added after first call'
    assert result(native_check, value) == result(canonical.reference_check, value)


def test_native_dictionary_insertion_orders_and_unicode_are_unmodified(native_check):
    left, right = {'z': 1, 'a': 'á'}, {'a': 'á', 'z': 1}
    assert result(native_check, left, encode=True) == result(native_check, right, encode=True)
    assert result(native_check, {'a': 'á'}, encode=True) != result(native_check, {'a': 'a\u0301'}, encode=True)


def test_hook_uses_only_validated_loader_and_falls_back_when_unavailable(monkeypatch):
    loader = ModuleType('apps.safety.canonical_kernel_loader')
    calls = []
    def checked(value, depth=0):
        calls.append((value, depth))
        canonical.reference_check(value, depth)
        return True
    checked.try_check = checked
    loader.validated_kernel = lambda: checked
    monkeypatch.setitem(sys.modules, loader.__name__, loader)
    assert canonical.canonical_bytes({'a': True}) == b'{"a":true}'
    assert calls == [({'a': True}, 0)]
    loader.validated_kernel = lambda: None
    assert canonical.canonical_bytes({'a': True}) == b'{"a":true}'
    assert len(calls) == 1


def test_hook_does_not_swallow_integrity_or_nested_loader_import_errors(monkeypatch):
    loader = ModuleType('apps.safety.canonical_kernel_loader')
    class IntegrityError(Exception):
        pass
    def corrupted():
        raise IntegrityError('Synthetic installed manifest mismatch')
    loader.validated_kernel = corrupted
    monkeypatch.setitem(sys.modules, loader.__name__, loader)
    with pytest.raises(IntegrityError):
        canonical.canonical_bytes({'a': 1})
    def nested_missing():
        raise ModuleNotFoundError('Nested dependency missing', name='internal_missing_dependency')
    loader.validated_kernel = nested_missing
    with pytest.raises(ModuleNotFoundError) as error:
        canonical.canonical_bytes({'a': 1})
    assert error.value.name == 'internal_missing_dependency'


def test_native_custom_depth_comparison_and_addition_use_reference_fallback(native_check):
    class Depth:
        def __init__(self, value, events):
            self.value, self.events = value, events
        def __gt__(self, limit):
            self.events.append(('compare', self.value, limit))
            return self.value > limit
        def __add__(self, increment):
            self.events.append(('add', self.value, increment))
            return Depth(self.value + increment, self.events)
    native_events, reference_events = [], []
    assert result(native_check, [0], Depth(0, native_events)) == result(
        canonical.reference_check, [0], Depth(0, reference_events))
    assert native_events == reference_events


def test_native_dictionary_mutation_during_float_check_keeps_iterator_error(native_check, monkeypatch):
    native_finite = math.isfinite
    current = []
    def changed(value):
        current[0]['new'] = 1
        return native_finite(value)
    monkeypatch.setattr(math, 'isfinite', changed)
    current[:] = [{'a': 1.0}]
    expected = result(canonical.reference_check, current[0])
    current[:] = [{'a': 1.0}]
    assert result(native_check, current[0]) == expected
    assert expected[0] == 'rejected' and expected[1] is RuntimeError


def test_native_depth_boundary_rejects_before_bad_leaf_or_container_keys(native_check):
    for value in (object(), {1: 'bad key'}, [object()]):
        expected = result(canonical.reference_check, value, 201)
        assert expected == ('rejected', ValueError, 'Canonical JSON exceeds maximum nesting')
        assert result(native_check, value, 201) == expected


def test_native_first_failure_follows_original_dictionary_insertion_order(native_check):
    nonfinite_first = {'first': math.inf, 1: 'invalid key after first item'}
    key_first = {1: 'invalid first key', 'later': math.inf}
    for value in (nonfinite_first, key_first):
        assert result(native_check, value) == result(canonical.reference_check, value)
    assert result(native_check, nonfinite_first)[1] is ValueError
    assert result(native_check, key_first)[1] is TypeError


@pytest.mark.parametrize('entry', ['check', 'canonical'])
def test_original_caller_recursion_budget_in_subprocess(entry):
    """Low limits and deep callers compare the pre-hook body in equal frames."""
    import subprocess
    import textwrap

    script = textwrap.dedent('''
        import json, math, sys
        import orjson
        from apps.safety.fast_canonical import _check, canonical_bytes
        from apps.safety.canonical_kernel_loader import validated_kernel
        assert validated_kernel() is not None

        def original(value, depth=0):
            if depth > 200:
                raise ValueError("Canonical JSON exceeds maximum nesting")
            kind = type(value)
            if value is None or kind in (str, bool, int):
                return
            if kind is float:
                if not math.isfinite(value):
                    raise ValueError("Canonical JSON requires finite numbers")
                return
            if kind is dict:
                for key, item in value.items():
                    if type(key) is not str:
                        raise TypeError("Canonical JSON requires string keys")
                    original(item, depth + 1)
                return
            if kind in (list, tuple):
                for item in value:
                    original(item, depth + 1)
                return
            raise TypeError("Canonical JSON requires explicit JSON values")

        def original_bytes(value):
            original(value)
            return orjson.dumps(value, option=orjson.OPT_SORT_KEYS)

        def invoke(function, value, callers):
            if callers:
                return invoke(function, value, callers - 1)
            return function(value)

        def outcome(function, value, callers):
            try:
                result = invoke(function, value, callers)
                return ('accepted', repr(result))
            except Exception as error:
                return ('rejected', type(error).__name__, str(error))

        entry = sys.argv[1]
        left, right = (original, _check) if entry == 'check' else (original_bytes, canonical_bytes)
        comparisons = []
        for limit, callers, nesting in [(80, 0, 120), (100, 60, 30),
                                       (100, 60, 0), (80, 0, 5)]:
            value = 0
            for _ in range(nesting):
                value = [value]
            sys.setrecursionlimit(limit)
            a, b = outcome(left, value, callers), outcome(right, value, callers)
            sys.setrecursionlimit(1000)
            comparisons.append((a, b))
        assert all(a == b for a, b in comparisons), comparisons
        print(json.dumps({'matched': len(comparisons)}))
    ''')
    completed = subprocess.run([sys.executable, '-c', script, entry],
                               capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0, completed.stderr
    assert '"matched": 4' in completed.stdout


def test_native_direct_recursion_budget_in_subprocess():
    import subprocess
    import textwrap

    script = textwrap.dedent('''
        import sys
        from apps.safety.fast_canonical import reference_check
        from apps.safety.canonical_kernel_loader import validated_kernel
        kernel = validated_kernel()
        assert kernel is not None
        value = 0
        for _ in range(120):
            value = [value]
        sys.setrecursionlimit(80)
        outcomes = []
        for check in (reference_check, kernel):
            try:
                check(value)
                outcomes.append(('accepted',))
            except Exception as error:
                outcomes.append((type(error).__name__, str(error)))
        sys.setrecursionlimit(1000)
        assert outcomes[0] == outcomes[1], outcomes
    ''')
    completed = subprocess.run([sys.executable, '-c', script], capture_output=True,
                               text=True, timeout=20)
    assert completed.returncode == 0, completed.stderr


def test_custom_metaclass_comparison_callbacks_match(native_check):
    events = []

    class Meta(type):
        def __eq__(cls, other):
            events.append(other.__name__)
            return False

    class Value(metaclass=Meta):
        pass

    expected = result(canonical.reference_check, Value())
    expected_events = events[:]
    events.clear()
    assert result(native_check, Value()) == expected
    assert events == expected_events
