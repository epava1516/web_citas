"""Accounting and verdict boundaries, plus fixed-drain behavior of real scheduling."""

import time

from scripts.benchmark_accounting import POLICY, counts, review, run_open_loop


def population(count=100):
    return [
        dict(
            id=f"d-{i}",
            scheduled_at=i / 20,
            emitted_at=i / 20 + 0.001,
            ended_at=i / 20 + 0.201,
            unexpected=False,
            timeout=False,
        )
        for i in range(count)
    ]


def test_strict_contract_thresholds_and_invalid_generator_are_distinct():
    rows = population()
    assert review(rows, duration=5, rps=20, policy=POLICY)["verdict"] == "PASS"
    rows[0].update(unexpected=True, timeout=True)
    result = review(rows, duration=5, rps=20, policy=POLICY)
    assert result["verdict"] == "FAIL"  # Exactly1%, not below1%.
    assert result["counts"]["timeouts"] == result["counts"]["failed"] == 1
    rows[0].update(emitted_at=None, ended_at=None)
    result = review(rows, duration=5, rps=20, policy=POLICY)
    assert result["verdict"] == "INVALID"
    assert result["counts"]["reconciled"] and result["counts"]["not_emitted"] == 1
    rows = population()
    for row in rows:
        row["ended_at"] = row["emitted_at"] + 0.8
    assert review(rows, duration=5, rps=20, policy=POLICY)["verdict"] == "FAIL"
    rows = population()
    rows[-1].update(
        emitted_at=rows[-1]["scheduled_at"] + 0.2, ended_at=rows[-1]["scheduled_at"] + 0.4
    )
    assert review(rows, duration=5, rps=20, policy=POLICY)["verdict"] == "INVALID"


def test_error_latency_and_pending_are_not_hidden_by_success_population():
    rows = population(20)
    for row in rows[-2:]:
        row.update(unexpected=True, timeout=True, ended_at=row["emitted_at"] + 65)
    result = review(rows, duration=1, rps=20, policy=POLICY)
    assert result["observable_latency_seconds"]["p95"] == 65
    assert result["observable_latency_seconds"]["population"] == 20
    rows[0]["ended_at"] = None
    result = review(rows, duration=1, rps=20, policy=POLICY)
    assert result["verdict"] == "INVALID" and result["counts"]["pending"] == 1
    assert counts(rows)["reconciled"]


def test_fixed_drain_classifies_pending_and_late_response_cannot_rewrite_snapshot():
    def slow_fetch(path, **kwargs):
        time.sleep(0.30)
        return dict(status=200, unexpected=False)

    policy = {**POLICY, "drain_seconds": 0.05}
    started = time.monotonic()
    result = run_open_loop(
        slow_fetch, ["/slow/"], duration=0.1, rps=10, upload_specs=[], policy=policy
    )
    assert time.monotonic() - started < 0.28
    assert result["window_close"]["dynamic"]["pending"] == 1
    assert result["final_before_deadline_classification"]["dynamic"]["pending"] == 1
    assert result["counts"]["pending"] == 0
    assert result["counts"]["failed"] == result["counts"]["timeouts"] == 1
    assert result["samples"][0]["forced_terminal"]
    time.sleep(0.20)
    assert result["counts"]["failed"] == 1 and result["samples"][0]["error"] == "drain_deadline"
