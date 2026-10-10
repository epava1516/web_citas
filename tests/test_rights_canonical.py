"""Serialization/content identity checks; no PostgreSQL integration claim."""

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from apps.safety.fast_canonical import canonical, canonical_bytes, content_reference
from apps.safety.rights import fingerprint
from apps.safety.rights_portability_selection import row_reference


def test_sorted_unicode_and_supported_numbers_roundtrip():
    value = {"🙂": [-(2**63), 2**64 - 1, 0, -0.0, 1.25, True, None], "á": "漢字"}
    encoded = canonical_bytes(value)
    assert encoded == canonical_bytes(dict(reversed(list(value.items()))))
    assert json.loads(encoded) == value
    assert canonical(value).encode() == encoded
    assert b"\\u" not in encoded
    assert content_reference(value).startswith("b3v2:")
    assert content_reference(value) == content_reference(json.loads(encoded))


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_numbers_never_collapse_to_null(number):
    with pytest.raises(ValueError, match="finite"):
        canonical({"nested": [number]})


@pytest.mark.parametrize(
    "value",
    [datetime.now(timezone.utc), Decimal("1.25"), UUID(int=1), {1: "ambiguous"}, b"bytes", {"set"}],
)
def test_non_json_types_require_explicit_conversion(value):
    with pytest.raises(TypeError):
        canonical(value)


@pytest.mark.parametrize("value", [-(2**63) - 1, 2**64])
def test_out_of_range_integer_rejected(value):
    with pytest.raises(TypeError):
        canonical(value)


def test_unicode_is_not_normalized_and_cycles_are_rejected():
    assert content_reference("é") != content_reference("e\u0301")
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError, match="nesting"):
        canonical(cyclic)


def test_content_reference_binds_dataset_position_and_entire_row():
    original = row_reference("revisions", 0, {"description": "one", "title": "two"})
    assert original == row_reference("revisions", 0, {"title": "two", "description": "one"})
    assert original != row_reference("revisions", 1, {"description": "one", "title": "two"})
    assert original != row_reference("profile", 0, {"description": "one", "title": "two"})
    assert original != row_reference("revisions", 0, {"description": "changed", "title": "two"})


def test_action_fingerprint_still_keyed_and_distinct_from_content(settings):
    payload = canonical({"reason": "Synthetic reviewed authority", "actor": 123})
    first = fingerprint(payload)
    settings.SECRET_KEY = "different-synthetic-test-key"
    assert fingerprint(payload) != first
    assert len(first) == 64 and not first.startswith("b3v2:")


def test_canonical_utf8_bytes_keep_the_keyed_fingerprint():
    from apps.safety.rights import fingerprint

    value = {"source": ["á漢字\u2028", {"é": "verified synthetic Unicode"}]}
    assert fingerprint(canonical_bytes(value)) == fingerprint(canonical(value))
