import pytest
from django.core.exceptions import ValidationError

from apps.safety.recipient_assessments import targets, validate_decisions


def fixture_data(acknowledged=False):
    # Pure schema fixture, not a delivered notification or verified account.
    return {
        "candidates": [{"kind": "account", "reference": "synthetic-account", "evidence": []}],
        "pending": ["unidentified_audience"],
        "manager_notices": [
            {
                "recipient_id": "synthetic-account",
                "acknowledged_at": "synthetic-date" if acknowledged else None,
            }
        ],
    }


def decisions(data):
    return {
        key: {
            "outcome": "pending",
            "reason": "Synthetic grounded assessment for schema validation",
            "evidence": "Synthetic evidence awaiting independent review",
        }
        for key in targets(data)
    }


def test_every_candidate_and_gap_needs_reason_and_evidence():
    data = fixture_data()
    values = decisions(data)
    assert validate_decisions(data, values) == values
    values.pop("gap:unidentified_audience")
    with pytest.raises(ValidationError):
        validate_decisions(data, values)
    values = decisions(data)
    values["gap:unidentified_audience"]["evidence"] = ""
    with pytest.raises(ValidationError):
        validate_decisions(data, values)


def test_communication_requires_matching_recorded_receipt_not_free_text():
    data = fixture_data()
    values = decisions(data)
    target = next(key for key in targets(data) if not key.startswith("gap:"))
    values[target]["outcome"] = "communicated"
    with pytest.raises(ValidationError):
        validate_decisions(data, values)
    assert validate_decisions(fixture_data(True), values) == values
    values["gap:unidentified_audience"]["outcome"] = "communicated"
    with pytest.raises(ValidationError):
        validate_decisions(fixture_data(True), values)
