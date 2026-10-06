import base64
import hashlib
import json
import os
import subprocess
import sys
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
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
@pytest.mark.parametrize("scoped", [False, True, "combined", "metadata", "physical"])
def test_audited_subject_snapshot_includes_only_profile_history_and_cannot_claim_complete(
    request, settings, monkeypatch, tmp_path, account_only, scoped
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
    if scoped:
        from scripts.collect_access_resource_logs import scoped_origin_name
        from scripts.scope_retained_redis_origin import scoped_body

        directory_path = tmp_path / "origins"
        directory_path.mkdir(mode=0o700)
        env = os.environ.copy()
        database = connection.settings_dict
        env.update(
            POSTGRES_DB=database["NAME"], POSTGRES_USER=database["USER"],
            POSTGRES_PASSWORD=database["PASSWORD"], DB_HOST=database["HOST"],
            DB_PORT=str(database["PORT"]), DJANGO_SECRET_KEY=settings.SECRET_KEY,
            SAFETY_ENCRYPTION_KEY=settings.SAFETY_ENCRYPTION_KEY,
        )
        args = [sys.executable, "-m", "scripts.scope_retained_redis_origin", "--origin", str(path),
                "--output-directory", str(directory_path), "--request", str(case.pk),
                "--inventory", str(inventory.pk)]
        if scoped in {"combined", "metadata", "physical"}:
            from retained_rdb_fixture import capture, native_decoder

            rdb_body, _ = capture(tmp_path / "native", inventory.created_at, [message(blob), message(str(uuid4()))])
            rdb_path = tmp_path / "snapshot.encrypted"
            rdb_path.write_text(seal(rdb_body))
            rdb_path.chmod(0o600)
            decoder, decoder_digest = native_decoder()
            args.extend(["--origin", str(rdb_path), "--decoder", str(decoder), "--decoder-sha256", decoder_digest])
            if scoped in {"metadata", "physical"}:
                from retained_rdb_fixture import aux_decoder

                if scoped == "physical":
                    from retained_rdb_fixture import metadata_decoder

                    aux, aux_hash = metadata_decoder()
                    args.extend(["--metadata-decoder", str(aux), "--metadata-decoder-sha256", aux_hash])
                else:
                    aux, aux_hash = aux_decoder()
                    args.extend(["--aux-decoder", str(aux), "--aux-decoder-sha256", aux_hash])
        completed = subprocess.run(args, env=env, capture_output=True, timeout=30, check=True)
        assert json.loads(completed.stdout)["coverage_accepted"] is False
        path = directory_path / scoped_origin_name("redis-history", case.pk, inventory.pk)
        original_ciphertext = path.read_bytes()
        wrong = args.copy()
        wrong[wrong.index("--request") + 1] = str(uuid4())
        rejected = subprocess.run(wrong, env=env, capture_output=True, timeout=30)
        assert rejected.returncode == 2 and path.read_bytes() == original_ciphertext
        body = unseal(path.read_text()) if scoped in {"combined", "metadata", "physical"} else scoped_body(body, inventory)
        settings.ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE = str(directory_path)
    else:
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
        expected_pending = [
            "historical_redis_coverage",
            "historical_result_payload_review",
        ]
        if scoped in {"combined", "metadata", "physical"}:
            expected_pending.append("snapshot_metadata_scope_review")
        assert original["redis_history"]["pending"] == expected_pending
        assert len(original["groups"]["operations.TaskResultHistory"]) == 1
    assert len(original["redis_history"]["records"]) == (0 if account_only else (2 if scoped in {"combined", "metadata", "physical"} else 1))
    reason = "Synthetic reviewed historical scope, no assertion of exhaustive infrastructure"
    decisions = {
        "models": {model: {"status": "omitted", "reason": reason} for model in original["groups"]},
        "resources": {"status": "reviewed", "reason": reason},
    }
    if scoped in {"metadata", "physical"}:
        with pytest.raises(ValidationError, match="infrastructure scope"):
            compile_package(inventory, SimpleNamespace(pk=uuid4()), original, decisions, cutoff=inventory.created_at, projected=projected)
        decisions["resources"]["redis_metadata_digest"] = "altered"
        with pytest.raises(ValidationError, match="metadata review digest"):
            compile_package(inventory, SimpleNamespace(pk=uuid4()), original, decisions, cutoff=inventory.created_at, projected=projected)
        decisions["resources"]["redis_metadata_digest"] = original["redis_history"]["metadata_digest"]
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
    if scoped in {"metadata", "physical"}:
        assert package["review_material"]["redis_history"]["metadata_review"]
        assert "metadata_review" not in str(package["copy"])
        assert "snapshot_metadata_scope_review" in package["pending"]
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
