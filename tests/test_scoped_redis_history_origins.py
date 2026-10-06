"""Real private files keep partial Redis origins isolated by case and inventory."""

import base64
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from test_redis_history_scope import message
from test_redis_retained_history import command

from apps.safety.crypto import seal, unseal
from apps.safety.redis_history_scope import history_records
from scripts.scope_retained_redis_origin import prepare_origin, prepare_origins


def origins(tmp_path, settings):
    tmp_path.chmod(0o700)
    settings.ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE = str(tmp_path)
    settings.CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": "fixture:"}
    settings.CELERY_TASK_DEFAULT_QUEUE = "q"
    now = timezone.now()
    own, other = str(uuid4()), str(uuid4())
    raw = command(b"LPUSH", b"fixture:q", message(own), message(other))
    body = {
        "schema": "local-redis-aof-origin-v1", "project": "web-modelos",
        "captured_at": now.isoformat(), "sha256": hashlib.sha256(raw).hexdigest(),
        "content_base64": base64.b64encode(raw).decode(), "partial": True,
    }
    source = tmp_path / "capture.encrypted"
    source.write_text(seal(body))
    source.chmod(0o600)
    case = SimpleNamespace(pk=uuid4())
    inventory = SimpleNamespace(
        pk=1, request_id=case.pk, source_digest="1" * 64, created_at=now,
    )
    return source, case, inventory, own, other


def read(settings, case, inventory, blobs):
    return history_records(blobs, inventory.created_at, case=case, inventory=inventory)


def test_independent_slots_preserve_previous_inventory_and_filter_subject(tmp_path, settings):
    source, first, inventory, own, other = origins(tmp_path, settings)
    path = prepare_origin(source, tmp_path, inventory)
    previous = path.read_bytes()
    original = read(settings, first, inventory, {own})
    second = SimpleNamespace(pk=uuid4())
    later = SimpleNamespace(
        pk=2, request_id=second.pk, source_digest="2" * 64,
        created_at=inventory.created_at + timedelta(seconds=1),
    )
    other_path = prepare_origin(source, tmp_path, later)
    assert other_path != path and path.read_bytes() == previous
    assert read(settings, first, inventory, {own}) == original
    foreign = read(settings, second, later, {other})
    assert len(original["records"]) == len(foreign["records"]) == 1
    assert original["origin_digest"] != foreign["origin_digest"]
    assert original["records"] != foreign["records"]
    assert original["partial"] and original["pending"] == ["historical_redis_coverage"]
    assert own not in str(original) and other not in str(original)
    with pytest.raises(ValidationError):
        history_records({own}, inventory.created_at)


@pytest.mark.parametrize("field", ["request", "inventory", "source_digest", "cutoff", "schema"])
def test_wrong_scoped_body_is_rejected_even_in_correct_slot(tmp_path, settings, field):
    source, case, inventory, own, _ = origins(tmp_path, settings)
    path = prepare_origin(source, tmp_path, inventory)
    body = unseal(path.read_text())
    if field == "schema":
        body = {key: value for key, value in body.items() if key not in {"request", "inventory", "source_digest", "cutoff"}}
        body["schema"] = "local-redis-aof-origin-v1"
    else:
        body[field] = True if field == "inventory" else "altered"
    path.write_text(seal(body))
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


def test_owned_private_origin_cutoff_and_permissions_are_required(tmp_path, settings):
    source, case, inventory, own, _ = origins(tmp_path, settings)
    future = unseal(source.read_text())
    future["captured_at"] = (inventory.created_at + timedelta(seconds=1)).isoformat()
    source.write_text(seal(future))
    with pytest.raises(ValueError):
        prepare_origin(source, tmp_path, inventory)
    future["captured_at"] = inventory.created_at.isoformat()
    source.write_text(seal(future))
    source.chmod(0o644)
    with pytest.raises(ValueError):
        prepare_origin(source, tmp_path, inventory)
    source.chmod(0o600)
    path = prepare_origin(source, tmp_path, inventory)
    path.chmod(0o644)
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})
    path.chmod(0o600)
    tmp_path.chmod(0o755)
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


def test_competing_writers_do_not_overwrite_the_accepted_origin(tmp_path, settings):
    source, case, inventory, own, _ = origins(tmp_path, settings)

    def write():
        try:
            return prepare_origin(source, tmp_path, inventory)
        except FileExistsError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: write(), range(2)))
    assert len([path for path in outcomes if path is not None]) == 1
    assert len(read(settings, case, inventory, {own})["records"]) == 1


def test_valid_encryption_with_non_object_json_is_rejected_as_invalid_origin(tmp_path, settings):
    source, case, inventory, own, _ = origins(tmp_path, settings)
    path = prepare_origin(source, tmp_path, inventory)
    path.write_text(seal(["schema", "project", "captured_at", "sha256", "content_base64", "partial"]))
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


def test_producer_rejects_non_object_origin_without_creating_destination(tmp_path, settings):
    source, _, inventory, _, _ = origins(tmp_path, settings)
    source.write_text(seal(["schema"]))
    before = set(tmp_path.iterdir())
    with pytest.raises(ValueError, match="Retained origin object required"):
        prepare_origins([source], tmp_path, inventory)
    assert set(tmp_path.iterdir()) == before
