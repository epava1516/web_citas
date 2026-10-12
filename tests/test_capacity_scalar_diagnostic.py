"""Instrumentation forwarding and original pure corpus; no database verification here."""

import gc
import json
import sys
from types import ModuleType

import pytest
from django.core.exceptions import ValidationError

from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_selection import pointer_value
from tests.capacity_chain_diagnostic import Collector
from tests.capacity_scalar_diagnostic import benchmark, counted_leaves, observed, scope, statistics


def test_structural_census_matches_original_leaves_without_values():
    rows = [{"a/b": {"~": [1, None]}, "empty": [], "flag": True}, {}]
    census = statistics(rows)
    leaves = [leaf for row in rows for leaf in scalar_fields(row)]
    assert census["leaves"] == len(leaves) == 3
    assert census["rows"] == 2 and census["containers"] == 5
    assert census["empty_containers"] == 2 and census["escaped_keys"] == 2
    assert census["max_depth"] == 3 and census["sum_leaf_depth"] == 7
    assert census["sum_path_chars"] == sum(len(item["path"]) for item in leaves)
    assert census["leaf_types"] == {"int": 1, "NoneType": 1, "bool": 1}
    assert "value" not in census


def test_alias_counts_root_consumption_without_patching_recursion():
    collector = Collector()
    collector.sites = {}
    value = {"a": {"b": [1, 2]}}
    wrapper = counted_leaves(scalar_fields, "consumer", collector)
    assert list(wrapper(value)) == list(scalar_fields(value))
    assert sum(item["calls"] for item in collector.sites.values()) == 1
    assert sum(item["leaves_yielded"] for item in collector.sites.values()) == 2
    iterator = wrapper(value)
    assert next(iterator)["value"] == 1
    iterator.close()


def test_consumer_span_forwards_failure_and_cleans_stack():
    collector = Collector()
    collector.mode = "spans"

    def fail(value):
        raise ValueError(value)

    with pytest.raises(ValueError, match="synthetic"):
        observed(fail, "probe", collector)("synthetic")
    assert collector.spans["probe"]["calls"] == 1 and not collector.stack


@pytest.mark.parametrize("mode", ["spans", "count"])
def test_scope_restores_regular_and_late_aliases_after_failure(mode, monkeypatch):
    from apps.safety import rights_portability_catalog, rights_portability_coverage

    original = rights_portability_coverage.compile_coverage
    scalar = rights_portability_catalog.scalar_fields
    late = ModuleType("apps.safety._scalar_test_late")
    monkeypatch.setitem(sys.modules, late.__name__, late)
    with pytest.raises(ValueError):
        with scope(mode):
            late.operation = rights_portability_coverage.compile_coverage
            assert late.operation is not original
            assert rights_portability_catalog.scalar_fields is scalar
            with pytest.raises(RuntimeError):
                with scope(mode):
                    pytest.fail("Nested diagnosis must fail")
            raise ValueError("synthetic")
    assert rights_portability_coverage.compile_coverage is original
    assert late.operation is original
    assert rights_portability_coverage.scalar_fields is scalar


def test_original_aa_preserves_corpus_gc_and_reports_consumption_perimeters():
    row = {"a/b": [1, {"~": "synthetic"}]}
    enabled, thresholds = gc.isenabled(), gc.get_threshold()
    result = benchmark([row, {}], [(row, "/a~1b/1/~0")])
    assert len(result["samples"]) == 60
    assert all(item["result_count"] == (1 if item["operation"] == "selected_pointers" else 2)
               for item in result["samples"])
    assert gc.isenabled() == enabled and gc.get_threshold() == thresholds
    assert row == {"a/b": [1, {"~": "synthetic"}]}


def test_original_edge_domain_is_not_json_normalized():
    class DictSubclass(dict):
        pass

    class ListSubclass(list):
        pass

    class StrSubclass(str):
        pass

    value = DictSubclass({StrSubclass("~01/"): ListSubclass([True, None, (1, 2), float("inf")])})
    leaves = list(scalar_fields(value))
    assert [item["path"] for item in leaves] == ["/~001~1/" + str(i) for i in range(4)]
    assert leaves[2]["value"] is value["~01/"][2]  # tuple is a scalar for this public API
    assert type(pointer_value(value, "/~001~1/0")) is bool
    with pytest.raises(ValidationError, match="requires an object or list"):
        list(scalar_fields(42))
    with pytest.raises(ValidationError, match="object key"):
        list(scalar_fields({"valid": 1, 2: 3}))
    for path in ("/01", "/-", "/2", "/~2", "/~"):
        with pytest.raises(ValidationError):
            pointer_value([1, 2], path)
    assert pointer_value({"x" * 499: 1}, "/" + "x" * 499) == 1
    with pytest.raises(ValidationError, match="field path"):
        pointer_value({"x" * 500: 1}, "/" + "x" * 500)


def test_original_generator_mutation_close_throw_and_depth_are_preserved():
    value = {"a": 1, "b": 2}
    generator = scalar_fields(value)
    assert next(generator)["value"] == 1
    value["b"] = 3
    assert next(generator)["value"] == 3
    generator.close()
    generator = scalar_fields(value)
    next(generator)
    with pytest.raises(ValueError, match="injected"):
        generator.throw(ValueError("injected"))
    deep = {"end": 1}
    for _ in range(sys.getrecursionlimit() + 20):
        deep = {"child": deep}
    with pytest.raises(RecursionError):
        list(scalar_fields(deep))


def test_original_wide_deep_escape_aa_baseline(record_property):
    wide = {f"field-{index}": str(index) for index in range(256)}
    deep = {"leaf": "synthetic"}
    for _ in range(64):
        deep = {"child": deep}
    escaped = {"~01/": [True, None]}
    rows = [wide, deep, escaped, {"empty": []}]
    census = statistics(rows)
    before = [list(scalar_fields(row)) for row in rows]
    result = benchmark(rows, [(wide, "/field-0"), (deep, "/child" * 64 + "/leaf"),
                              (escaped, "/~001~1/0")])
    assert [list(scalar_fields(row)) for row in rows] == before
    assert statistics(rows) == census
    assert census["max_depth"] == 65 and census["leaves"] == 259
    record_property("scalar_edge_original_AA", json.dumps(dict(census=census, benchmark=result)))
