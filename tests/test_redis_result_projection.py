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
