"""Pure exclusion optimization preserves the established assessment contract."""

from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError

from apps.safety import rights_portability as portability
from apps.safety import rights_portability_coverage as coverage


def facts():
    return dict(
        status="excluded",
        basis="other",
        origin="provided",
        automated=True,
        subject_related=True,
        third_party_reviewed=True,
        reason="Synthetic documented exclusion reason",
        evidence="Synthetic documented exclusion evidence",
    )


def changed(**changes):
    value = facts()
    value.update(changes)
    return value


def old_exclusion(value):
    if not isinstance(value, dict) or value.get("status") != "excluded":
        raise ValidationError("Document a definite exclusion, not an unknown omission")
    return portability.checked_assessment({name: value for name in portability.DATASETS})[
        portability.DATASETS[0]
    ]


def outcome(operation, value):
    try:
        return "valid", operation(deepcopy(value))
    except ValidationError as error:
        return "invalid", error.messages


def test_all_provenance_and_nullable_combinations_match_previous_exclusion():
    for basis in sorted(portability.BASES):
        for origin in sorted(portability.ORIGINS):
            for automated in (True, False, None):
                for related in (True, False, None):
                    value = changed(
                        basis=basis,
                        origin=origin,
                        automated=automated,
                        subject_related=related,
                        third_party_reviewed=None,
                    )
                    assert outcome(coverage.exclusion, value) == outcome(old_exclusion, value)
                    expected_valid = (
                        basis in {"legal_obligation", "legitimate_interest", "other"}
                        or origin in {"inferred", "third_party"}
                        or automated is False
                        or related is False
                    )
                    assert (outcome(coverage.exclusion, value)[0] == "valid") is expected_valid


def test_exclusion_validates_once_assessment_still_nine_and_does_not_mutate(monkeypatch):
    value = facts()
    before = deepcopy(value)
    original = portability._validate_decision
    calls = []

    def validate(item):
        calls.append(item)
        return original(item)

    monkeypatch.setattr(portability, "_validate_decision", validate)
    monkeypatch.setattr(coverage, "_validate_decision", validate)
    actual = coverage.exclusion(value)
    assert len(calls) == 1
    assert actual == before == value
    assert actual is not value
    actual["reason"] = "mutated output"
    assert value == before
    calls.clear()
    old_exclusion(value)
    assert len(calls) == 9


@pytest.mark.parametrize("status", ["pending", "eligible", "granular", "excluded"])
def test_all_statuses_keep_their_specific_conditions(status):
    value = changed(status=status)
    if status == "pending":
        value.update(reason="", evidence="", automated=None, subject_related=None)
    elif status == "eligible":
        value.update(basis="contract", origin="observed")
    elif status == "granular":
        value.update(origin="mixed")
    assert (
        portability.checked_assessment({name: value for name in portability.DATASETS})["profile"]
        == value
    )
    if status != "excluded":
        with pytest.raises(ValidationError, match="Document a definite exclusion"):
            coverage.exclusion(value)


def test_eligible_and_granular_facts_are_not_weakened():
    for basis in ("consent", "contract"):
        for origin in ("provided", "observed"):
            eligible = changed(status="eligible", basis=basis, origin=origin)
            portability._validate_decision(eligible)
            for field in ("automated", "subject_related", "third_party_reviewed"):
                for value in (False, None):
                    with pytest.raises(ValidationError, match="Dataset does not meet portability"):
                        portability._validate_decision(dict(eligible, **{field: value}))
    for automated in (False, None):
        with pytest.raises(ValidationError, match="Granular assessment requires"):
            portability._validate_decision(
                changed(status="granular", origin="mixed", automated=automated)
            )


@pytest.mark.parametrize("field", ["automated", "subject_related", "third_party_reviewed"])
def test_boolean_facts_require_exact_bool_or_none(field):
    for value in (True, False, None):
        portability._validate_decision(changed(**{field: value}))
    for value in (0, 1, "true", [], {}):
        with pytest.raises(ValidationError, match="Portability facts require boolean or unknown"):
            portability._validate_decision(changed(**{field: value}))


@pytest.mark.parametrize("field", ["reason", "evidence"])
def test_text_type_strip_and_length_bounds_preserved(field):
    for value in ("x" * 20, "x" * 2000, " " + "x" * 20 + " "):
        assert coverage.exclusion(changed(**{field: value}))[field] == value
    for value, message in (
        (None, "Invalid portability evidence text"),
        ("x" * 2001, "Invalid portability evidence text"),
        (" " * 20, "Decided portability requires evidence and reason"),
        ("x" * 19, "Decided portability requires evidence and reason"),
    ):
        with pytest.raises(ValidationError, match=message):
            coverage.exclusion(changed(**{field: value}))
        assert outcome(coverage.exclusion, changed(**{field: value})) == outcome(
            old_exclusion, changed(**{field: value})
        )


def test_schema_labels_provenance_and_error_order_are_unchanged():
    cases = [
        (None, "Invalid portability decision schema"),
        ({}, "Invalid portability decision schema"),
        (dict(facts(), extra="forbidden"), "Invalid portability decision schema"),
        (changed(status=1, basis="bad"), "Invalid portability labels"),
        (changed(status="bad", basis="bad"), "Invalid portability status"),
        (changed(basis="bad", automated=1), "Invalid portability provenance"),
        (changed(automated=1, reason=None), "Portability facts require boolean or unknown"),
        (changed(status="pending", reason=None), "Invalid portability evidence text"),
        (changed(status="granular", origin="provided"), "Granular assessment requires"),
        (changed(status="excluded", basis="contract"), "Unknown or mixed provenance"),
        (changed(status="eligible", basis="other"), "Dataset does not meet portability"),
    ]
    for value, message in cases:
        with pytest.raises(ValidationError, match=message):
            portability._validate_decision(value)


def test_assessment_top_guard_insertion_order_and_deepcopy_aliasing_preserved():
    with pytest.raises(ValidationError, match="Assess every portability dataset"):
        portability.checked_assessment({"profile": None})
    shared = facts()
    assessment = {name: shared for name in reversed(portability.DATASETS)}
    actual = portability.checked_assessment(assessment)
    assert list(actual) == list(assessment)
    assert actual["profile"] is actual["revisions"]
    assert actual["profile"] is not shared
    actual["profile"]["reason"] = "mutable output"
    assert shared["reason"] != "mutable output"
    distinct = {name: facts() for name in portability.DATASETS}
    result = portability.checked_assessment(distinct)
    assert result["profile"] is not result["revisions"]
    assessment["representation_history"] = changed(status="pending", reason=None)
    assessment["profile"] = changed(status="bad")
    with pytest.raises(ValidationError, match="Invalid portability evidence text"):
        portability.checked_assessment(assessment)
