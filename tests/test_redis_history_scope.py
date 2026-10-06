import base64
import hashlib
import json
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_redis_retained_history import command
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import seal
from apps.safety.redis_history_scope import history_records, scoped_history


def message(blob):
    return json.dumps(
        {
            "content-type": "application/json",
            "content-encoding": "utf-8",
            "properties": {"body_encoding": "base64"},
            "headers": {
                "task": "apps.mediafiles.tasks.process_blob",
                "retries": 0,
                "id": "private-task-id-" + blob,
            },
            "body": base64.b64encode(json.dumps([[blob], {}, {}]).encode()).decode(),
        }
    ).encode()


def test_exact_owned_historical_messages_exclude_foreign_database_queue_and_capabilities():
    own, other = str(uuid4()), str(uuid4())
    raw = command(b"SELECT", b"0") + command(b"LPUSH", b"fixture:q", message(own), message(other))
    raw += command(
        b"HSET",
        b"fixture:unacked",
        b"private-tag",
        json.dumps([json.loads(message(own)), "", "q"]).encode(),
    )
    raw += command(b"LPUSH", b"other:q", message(own))
    raw += command(b"SELECT", b"1") + command(b"LPUSH", b"fixture:q", message(own))
    result = scoped_history(
        raw, {own}, prefix="fixture:", queue="q", origin_digest="private-origin"
    )
    assert len(result["records"]) == 2 and not result["blocked"]
    assert {r["data"]["state"] for r in result["records"]} == {"queued", "reserved"}
    assert all(
        r["data"]["historical"] and not r["data"]["original_time_known"] for r in result["records"]
    )
    assert other not in str(result) and own not in str(result)
    assert "private-task-id" not in str(result) and "private-tag" not in str(result)
    assert result["records"][0]["reference"] != result["records"][1]["reference"]


def test_unknown_or_large_scoped_messages_stay_blocked():
    raw = command(b"LPUSH", b"fixture:q", b"x" * (256 * 1024 + 1))
    result = scoped_history(raw, set(), prefix="fixture:", queue="q", origin_digest="origin")
    assert result["blocked"] == ["unsupported_historical_message"] and not result["records"]
    truncated = scoped_history(
        raw[:-1], set(), prefix="fixture:", queue="q", origin_digest="origin"
    )
    assert "incomplete_argument" in truncated["blocked"]


def test_encrypted_history_reader_binds_source_cutoff_and_preserves_partial(settings, tmp_path):
    blob = str(uuid4())
    raw = command(b"LPUSH", b"fixture:q", message(blob))
    now = timezone.now()
    body = {
        "schema": "local-redis-aof-origin-v1",
        "project": "web-modelos",
        "captured_at": now.isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_base64": base64.b64encode(raw).decode(),
        "partial": True,
    }
    path = tmp_path / "history.encrypted"
    path.write_text(seal(body))
    path.chmod(0o600)
    settings.ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE = str(path)
    settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": "fixture:"}
    settings.CELERY_TASK_DEFAULT_QUEUE = "q"
    read = history_records({blob}, now)
    assert read["configured"] and len(read["records"]) == 1
    assert read["pending"] == ["historical_redis_coverage"]
    with pytest.raises(ValidationError):
        history_records({blob}, now - timedelta(seconds=1))
    path.write_text(seal(body | {"sha256": "altered"}))
    with pytest.raises(ValidationError):
        history_records({blob}, now)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("account_only", [False, True])
def test_audited_subject_snapshot_includes_only_profile_history_and_cannot_claim_complete(
    request, settings, monkeypatch, tmp_path, account_only
):
    from types import SimpleNamespace

    from django.db import transaction
    from test_rights_information_export import approved_information

    from apps.safety.crypto import unseal
    from apps.safety.rights_access_delivery import compile_package, recipient_payload, snapshot
    from apps.safety.rights_access_scope_store import inspect
    from apps.safety.rights_exports import source_copy

    case, author, _, _, _, person, _, _, _, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    from django.contrib.auth.models import Permission

    from apps.core.models import User

    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    inventory, _ = inspect(
        author,
        case.pk,
        case.version,
        case.response_version,
        uuid4(),
        "Inspect synthetic scoped historical broker evidence",
    )
    manifest = unseal(inventory.encrypted_inventory)
    blob = manifest["media"][0]["blob"] if manifest["media"] else str(uuid4())
    raw = command(b"LPUSH", b"fixture:q", message(blob), message(str(uuid4())))
    result_id = "private-task-id-" + blob
    raw += command(
        b"SET",
        ("celery-task-meta-" + result_id).encode(),
        json.dumps(
            {"task_id": result_id, "status": "SUCCESS", "result": "PRIVATE RESULT PAYLOAD"}
        ).encode(),
    )
    body = {
        "schema": "local-redis-aof-origin-v1",
        "project": "web-modelos",
        "captured_at": inventory.created_at.isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_base64": base64.b64encode(raw).decode(),
        "partial": True,
    }
    path = tmp_path / "history.encrypted"
    path.write_text(seal(body))
    path.chmod(0o600)
    settings.ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE = str(path)
    settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": "fixture:"}
    settings.CELERY_TASK_DEFAULT_QUEUE = "q"
    with transaction.atomic():
        projected = source_copy(person, person.listing if person else None, case)
        original = snapshot(
            case,
            None if account_only else person,
            inventory,
            cutoff=inventory.created_at,
            projected=projected,
        )
    if account_only:
        assert not original["blocked"]
        assert "operations.TaskResultHistory" not in original["groups"]
    else:
        assert not original["blocked"]
        assert original["redis_history"]["pending"] == [
            "historical_redis_coverage",
            "historical_result_payload_review",
        ]
        assert len(original["groups"]["operations.TaskResultHistory"]) == 1
    assert len(original["redis_history"]["records"]) == (0 if account_only else 1)
    reason = "Synthetic reviewed historical scope, no assertion of exhaustive infrastructure"
    decisions = {
        "models": {model: {"status": "omitted", "reason": reason} for model in original["groups"]},
        "resources": {"status": "reviewed", "reason": reason},
    }
    if not account_only:
        decisions["models"]["operations.QueueHistory"] = {"status": "included", "reason": reason}
        decisions["models"]["operations.TaskResultHistory"] = {
            "status": "included",
            "reason": reason,
        }
    package = compile_package(
        inventory,
        SimpleNamespace(pk=uuid4()),
        original,
        decisions,
        cutoff=inventory.created_at,
        projected=projected,
    )
    assert package["partial"] and "historical_redis_coverage" in package["pending"]
    assert "private-task-id" not in str(package["copy"])
    assert "PRIVATE RESULT PAYLOAD" not in str(package)
    if not account_only:
        assert "historical_result_payload_review" in package["pending"]
        assert any(
            group["model"] == "operations.TaskResultHistory"
            for group in package["copy"]["additional_records"]
        )
    with pytest.raises(ValidationError):
        recipient_payload({"access_package": package})
    path.write_text(seal(body | {"content_base64": base64.b64encode(raw + b"altered").decode()}))
    with transaction.atomic(), pytest.raises(ValidationError):
        snapshot(
            case,
            None if account_only else person,
            inventory,
            cutoff=inventory.created_at,
            projected=projected,
        )
