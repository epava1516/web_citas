import hashlib
import json
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_rights_access_recipient_payload import synthetic_log_bundle

from apps.safety.crypto import seal, unseal
from apps.safety.rights_access_delivery import log_records
from apps.safety.rights_exports import canonical
from scripts.collect_access_resource_logs import signed_subject_log_event
from scripts.scope_retained_log_origins import prepare_origins


def origins(tmp_path, settings):
    tmp_path.chmod(0o700)
    settings.ACCESS_LOG_ORIGIN_BUNDLE = str(tmp_path)
    cutoff = timezone.now()
    case = SimpleNamespace(pk=uuid4())
    inventory = SimpleNamespace(pk=1, request_id=case.pk, source_digest="1" * 64, created_at=cutoff)
    event_at = cutoff - timedelta(minutes=5)
    event = signed_subject_log_event("account", "101", "profile_updated", "succeeded", event_at)
    paths = []
    for index in range(2):
        captured = cutoff - timedelta(minutes=2 - index)
        body = synthetic_log_bundle(captured, f"{event_at.isoformat()} {json.dumps(event)}\n")
        body["records"][0]["container_created_at"] = (event_at - timedelta(minutes=1)).isoformat()
        path = tmp_path / f"capture-{index}.encrypted"
        path.write_text(seal(body))
        path.chmod(0o600)
        paths.append(path)
    return paths, case, inventory


def test_historical_captures_keep_cutoffs_private_subject_projection_and_immutable_slots(
    tmp_path, settings
):
    paths, case, inventory = origins(tmp_path, settings)
    before = [path.read_bytes() for path in paths]
    output = prepare_origins(paths, tmp_path, inventory)
    result = log_records(
        set(), inventory.created_at, subjects={"account": {"101"}}, case=case, inventory=inventory
    )
    assert len(result["origins"]) == 12
    assert len(result["projected"]) == 2
    assert len({row["reference"] for row in result["projected"]}) == 2
    assert result["pending"][-1] == "historical_log_capture_coverage"
    assert all("subject_id" not in row["data"] and "signature" not in row["data"] for row in result["projected"])
    assert [path.read_bytes() for path in paths] == before
    with pytest.raises(FileExistsError):
        prepare_origins(paths, tmp_path, inventory)
    foreign = SimpleNamespace(pk=uuid4())
    other = SimpleNamespace(
        pk=2, request_id=foreign.pk, source_digest="2" * 64, created_at=inventory.created_at
    )
    original = output.read_bytes()
    other_output = prepare_origins(paths, tmp_path, other)
    other_result = log_records(
        set(), other.created_at, subjects={"account": {"102"}}, case=foreign, inventory=other
    )
    assert not other_result["projected"]
    assert other_output != output and output.read_bytes() == original


@pytest.mark.parametrize(
    "field", ["request", "inventory", "source_digest", "cutoff", "capture_sha256", "content"]
)
def test_historical_reader_rejects_changed_scope_or_content(tmp_path, settings, field):
    paths, case, inventory = origins(tmp_path, settings)
    output = prepare_origins(paths, tmp_path, inventory)
    body = unseal(output.read_text())
    if field == "capture_sha256":
        body["origins"][0][field] = "0" * 64
    elif field == "content":
        body["origins"][0]["capture"]["records"][0]["stdout"] += "altered"
    else:
        body[field] = True if field == "inventory" else "altered"
    output.write_text(seal(body))
    with pytest.raises(ValidationError):
        log_records(set(), inventory.created_at, case=case, inventory=inventory)


def test_historical_producer_rejects_duplicates_future_and_aggregate_limits(
    tmp_path, settings, monkeypatch
):
    from apps.safety import retained_log_origins
    from scripts import scope_retained_log_origins

    paths, case, inventory = origins(tmp_path, settings)
    with pytest.raises(ValueError, match="Duplicate"):
        prepare_origins([paths[0], paths[0]], tmp_path, inventory)
    monkeypatch.setattr(scope_retained_log_origins, "MAX_CONTENT_BYTES", 1)
    with pytest.raises(ValueError, match="aggregate"):
        prepare_origins(paths, tmp_path, inventory)
    monkeypatch.setattr(
        scope_retained_log_origins, "MAX_CONTENT_BYTES", retained_log_origins.MAX_CONTENT_BYTES
    )
    body = unseal(paths[0].read_text())
    body["captured_at"] = (inventory.created_at + timedelta(seconds=1)).isoformat()
    paths[0].write_text(seal(body))
    with pytest.raises(ValueError, match="outside inventory"):
        prepare_origins(paths, tmp_path, inventory)


def test_historical_reader_rejects_candidate_after_original_capture(tmp_path, settings):
    paths, case, inventory = origins(tmp_path, settings)
    output = prepare_origins(paths, tmp_path, inventory)
    body = unseal(output.read_text())
    capture = body["origins"][0]["capture"]
    content = f"{inventory.created_at.isoformat()} synthetic-subject@example.invalid late\n"
    capture["records"][0].update(
        stdout=content, stdout_sha256=hashlib.sha256(content.encode()).hexdigest()
    )
    body["origins"][0]["capture_sha256"] = hashlib.sha256(canonical(capture).encode()).hexdigest()
    output.write_text(seal(body))
    with pytest.raises(ValidationError):
        log_records(
            {"synthetic-subject@example.invalid"},
            inventory.created_at,
            case=case,
            inventory=inventory,
        )


def test_historical_preparation_bounds_serialized_envelope_before_writing(tmp_path, settings, monkeypatch):
    from apps.safety import retained_log_origins

    paths, case, inventory = origins(tmp_path, settings)
    monkeypatch.setattr(retained_log_origins, "MAX_CONTENT_BYTES", 1024)
    with pytest.raises(ValueError, match="serialized"):
        prepare_origins([paths[0]], tmp_path, inventory)
    assert not list(tmp_path.glob("access-logs-*.encrypted"))
