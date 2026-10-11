"""Synthetic alternate benchmark, never a latency acceptance gate."""

import json

import pytest

from tests import capacity_fingerprint_index_benchmark as experiment

pytestmark = pytest.mark.django_db(transaction=True)


def test_fingerprint_index_alternated_diagnostic(settings, record_property):
    settings.SECRET_KEY = "synthetic-fingerprint-benchmark"
    report = experiment.benchmark()
    assert report["status"] == "DIAGNOSTIC_NOT_REQUEST_GAIN"
    assert len(report["rows"]) == 24
    for row in report["rows"]:
        assert len(row["pairs"]) == 9
        for pair in row["pairs"]:
            for measured in pair.values():
                assert 0 <= measured["entries"] <= experiment.memo.MAX_ENTRIES
                assert measured["retained_bytes"] <= experiment.memo.MAX_INPUT_BYTES
                expected_calls = 1 if row["scenario"] in {"same-object", "fresh-hit"} else 8
                assert measured["native_calls"] == expected_calls
    record_property("fingerprint_index_diagnostic", json.dumps(report, separators=(",", ":")))
