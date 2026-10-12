"""Permanent differential oracle: path-only coverage preserves the public walk."""
import random
import sys

import pytest

from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_paths import _scalar_paths


def original(value, prefix=""):
    return {leaf["path"] for leaf in scalar_fields(value, prefix)}


def candidate(value, prefix=""):
    return {path for path in _scalar_paths(value, prefix)}


def outcome(operation, value, prefix=""):
    try:
        return ("ok", operation(value, prefix))
    except Exception as error:
        return (type(error), str(error) if not isinstance(error, RecursionError) else "depth")


@pytest.mark.parametrize("value,prefix", [
    ({"": 1, "~1": [None, {"/": True}], "/": [], "~": {}}, ""),
    ([1, {"a": (2, 3)}, float("nan"), float("inf")], ""),
    ({"valid": 1, 2: 3}, ""), (42, ""), (42, "/prefix"), ({}, ""), ([], ""),
])
def test_paths_match_values_order_sets_and_failures(value, prefix):
    def consume(value, prefix):
        return [leaf["path"] for leaf in scalar_fields(value, prefix)]
    assert outcome(consume, value, prefix) == outcome(lambda v, p: list(_scalar_paths(v, p)), value, prefix)
    assert outcome(original, value, prefix) == outcome(candidate, value, prefix)


def test_subclasses_custom_items_and_midstream_failures():
    class Text(str):
        def replace(self, *args):
            return Text(super().replace(*args))
    class Items(dict):
        def items(self):
            yield Text("~01/"), [1, 2]
            yield Text("~01/"), [3]
            raise ValueError("synthetic iterator failure")
    class Sequence(list):
        pass
    for walk in (scalar_fields, _scalar_paths):
        values = walk(Items())
        found = []
        with pytest.raises(ValueError, match="iterator failure"):
            for item in values:
                found.append(item["path"] if isinstance(item, dict) else item)
        assert found == ["/~001~1/0", "/~001~1/1", "/~001~1/0"]
    assert original(Sequence([{"": None}, (1, 2)])) == candidate(Sequence([{"": None}, (1, 2)]))


@pytest.mark.parametrize("kind", ["dict", "list"])
def test_lazy_mutation_send_close_and_throw(kind):
    for walk in (scalar_fields, _scalar_paths):
        child = {"a": 1, "b": 2} if kind == "dict" else [1, 2]
        value = {"nested": child}
        iterator = walk(value)
        first = next(iterator)
        assert (first["path"] if isinstance(first, dict) else first) == "/nested/" + ("a" if kind == "dict" else "0")
        if kind == "dict":
            child["c"] = 3
            with pytest.raises(RuntimeError):
                next(iterator)
        else:
            child.append(3)
            assert len(list(iterator)) == 2
        iterator.close()
        iterator = walk({"a": 1, "b": 2})
        next(iterator)
        second = iterator.send(None)
        assert (second["path"] if isinstance(second, dict) else second) == "/b"
        iterator.close()
        with pytest.raises(StopIteration):
            next(iterator)
        iterator = walk({"a": 1, "b": 2})
        next(iterator)
        with pytest.raises(ValueError, match="injected"):
            iterator.throw(ValueError("injected"))


def test_recursion_boundary_of_actual_consumers_and_cycles():
    # Same comprehension frames as compile_coverage, including the boundary.
    for depth in range(sys.getrecursionlimit() - 90, sys.getrecursionlimit() + 2):
        value = {"end": 1}
        for _ in range(depth):
            value = {"child": value}
        assert outcome(original, value) == outcome(candidate, value)
    cycle = []
    cycle.append(cycle)
    assert outcome(original, cycle) == outcome(candidate, cycle)


def test_randomized_json_shaped_tree_oracle_without_normalization():
    rng = random.Random(713)
    def tree(depth):
        if not depth or rng.randrange(3) == 0:
            return rng.choice([None, True, 3, "synthetic"])
        if rng.randrange(2):
            return [tree(depth-1) for _ in range(rng.randrange(5))]
        return {str(i)+rng.choice(["", "~", "/", "~1/"]): tree(depth-1)
                for i in range(rng.randrange(5))}
    for _ in range(250):
        value = {"": tree(5)}
        assert list(_scalar_paths(value)) == [leaf["path"] for leaf in scalar_fields(value)]
        assert candidate(value) == original(value)
