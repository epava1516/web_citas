import json
from uuid import uuid4

from test_redis_history_scope import message
from test_redis_retained_history import command

from apps.safety.redis_history_scope import scoped_history


def inspect(raw, own):
    return scoped_history(raw, {own}, prefix="fixture:", queue="q", origin_digest="origin")


def result(blob, **extra):
    task = "private-task-id-" + blob
    body = {
        "task_id": task,
        "status": "FAILURE",
        "result": "PRIVATE RESULT",
        "traceback": "PRIVATE TRACE",
        **extra,
    }
    return command(b"SET", ("celery-task-meta-" + task).encode(), json.dumps(body).encode())


def test_result_before_owned_message_is_associated_without_payload_disclosure():
    own = str(uuid4())
    raw = result(own) + command(b"LPUSH", b"fixture:q", message(own))
    data = inspect(raw, own)
    assert len(data["result_records"]) == 1
    assert data["result_records"][0]["data"]["state"] == "FAILURE"
    assert "historical_result_payload_review" in data["pending"]
    assert "PRIVATE" not in str(data) and own not in str(data)


def test_foreign_result_excluded_and_unlinked_result_remains_pending():
    own, other = str(uuid4()), str(uuid4())
    linked = inspect(result(other) + command(b"LPUSH", b"fixture:q", message(other)), own)
    assert not linked["result_records"] and not linked["blocked"]
    unlinked = inspect(result(other), own)
    assert not unlinked["result_records"]
    assert "unsupported_or_unassociated_historical_result" in unlinked["blocked"]


def test_conflicting_task_identity_prevents_result_attribution():
    own, other = str(uuid4()), str(uuid4())
    foreign = json.loads(message(other))
    foreign["headers"]["id"] = "private-task-id-" + own
    raw = command(
        b"LPUSH", b"fixture:q", message(own), json.dumps(foreign).encode(), message(own)
    ) + result(own)
    data = inspect(raw, own)
    assert not data["result_records"]
    assert "conflicting_historical_task_identity" in data["blocked"]


def test_extra_result_fields_and_identity_mismatch_block_without_disclosure():
    own = str(uuid4())
    queue = command(b"LPUSH", b"fixture:q", message(own))
    for extra in [{"private_field": "PRIVATE DATA"}, {"task_id": "different-id"}]:
        data = inspect(queue + result(own, **extra), own)
        assert not data["result_records"] and data["blocked"]
        assert "PRIVATE" not in str(data)


def periodic_message(task_id):
    import base64

    body = json.loads(message(str(uuid4())))
    body["headers"]["task"] = "apps.safety.tasks.purge_expired_access_response_drafts"
    body["headers"]["id"] = task_id
    body["body"] = base64.b64encode(json.dumps([[], {}, {}]).encode()).decode()
    return json.dumps(body).encode()


def test_typed_periodic_counter_is_accounted_for_without_subject_copy():
    own = str(uuid4())
    task_id = "private-task-id-" + own
    raw = result(own, status="SUCCESS", result=3, traceback=None) + command(
        b"LPUSH", b"fixture:q", periodic_message(task_id)
    )
    data = inspect(raw, own)
    assert (
        not data["records"]
        and not data["result_records"]
        and not data["blocked"]
        and not data["pending"]
    )
    assert len(data["technical_result_evidence"]) == 1
    assert (
        data["technical_result_evidence"][0]["reason"]
        == "known_periodic_counter_without_subject_arguments"
    )
    assert task_id not in str(data)


def test_periodic_payload_children_traceback_and_invalid_counts_remain_blocked():
    own = str(uuid4())
    queue = command(b"LPUSH", b"fixture:q", periodic_message("private-task-id-" + own))
    for change in [
        {"result": True},
        {"result": -1},
        {"result": 201},
        {"result": {"private": "PRIVATE"}},
        {"children": ["PRIVATE"]},
        {"traceback": "PRIVATE"},
        {"date_done": "PRIVATE"},
        {"date_done": "2026-10-06T12:00:00"},
    ]:
        fields = {"status": "SUCCESS", "result": 0, "traceback": None} | change
        data = inspect(queue + result(own, **fields), own)
        assert data["blocked"] and not data["technical_result_evidence"]
        assert "PRIVATE" not in str(data)
