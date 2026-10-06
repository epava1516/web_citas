"""Combined sources stay partial, scoped, and explicit about reconstruction."""

import base64
import hashlib
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from retained_rdb_fixture import aux_decoder, capture, native_decoder
from test_redis_history_scope import message
from test_scoped_redis_history_origins import origins, read

from apps.safety.crypto import seal, unseal
from scripts.decode_retained_rdb_origin import decode_body
from scripts.scope_retained_redis_origin import prepare_origins


def combined(tmp_path, settings, *, metadata=False):
    source, case, inventory, own, other = origins(tmp_path, settings)
    body, expiration = capture(tmp_path / "native", inventory.created_at, [message(own), message(other)])
    snapshot = tmp_path / "snapshot.encrypted"
    snapshot.write_text(seal(body))
    snapshot.chmod(0o600)
    decoder, digest = native_decoder()
    extra = {}
    if metadata:
        aux, aux_hash = aux_decoder()
        extra = {"aux_decoder": aux, "aux_decoder_sha256": aux_hash}
    path = prepare_origins([source, snapshot], tmp_path, inventory, decoder=decoder, decoder_sha256=digest, **extra)
    return path, case, inventory, own, other, body, expiration


def test_real_native_expired_snapshot_and_aof_keep_distinct_provenance(tmp_path, settings):
    path, case, inventory, own, other, body, expiration = combined(tmp_path, settings)
    before = path.read_bytes()
    result = read(settings, case, inventory, {own})
    assert len(result["records"]) == 2 and not result["blocked"]
    assert result["pending"] == ["historical_redis_coverage", "snapshot_metadata_scope_review"]
    assert result["partial"] and path.read_bytes() == before
    kinds = {row["data"]["source_kind"]: row for row in result["records"]}
    snapshot = kinds["rdb_snapshot_state"]["data"]
    assert snapshot["snapshot_captured_at"] == body["captured_at"]
    assert snapshot["snapshot_expiration_at"] == datetime.fromtimestamp(expiration / 1000, UTC).isoformat()
    assert expiration < datetime.now(UTC).timestamp() * 1000
    assert not snapshot["original_time_known"]
    assert "aof_command_history" in kinds
    assert own not in str(result) and other not in str(result)
    assert not list(Path("/tmp").glob("web-modelos-rdb-decode-*"))
    assert not Path("rdb-cli.log").exists()


def test_native_aux_is_bound_review_material_without_recipient_records(tmp_path, settings):
    _, case, inventory, own, other, _, _ = combined(tmp_path, settings, metadata=True)
    result = read(settings, case, inventory, {own})
    assert result["metadata_digest"] and len(result["metadata_review"]) == 1
    metadata = result["metadata_review"][0]
    assert len(metadata["records"]) == 5 and metadata["decision"] == "pending_independent_review"
    assert all(row["association"] == "infrastructure_scope_unreviewed" for row in metadata["records"])
    assert own not in str(metadata) and other not in str(metadata)
    assert "snapshot_metadata_scope_review" in result["pending"]
    assert len(result["records"]) == 2
    assert not list(Path("/tmp").glob("web-modelos-rdb-aux-*"))


@pytest.mark.parametrize("field", ["source_sha256", "source_origin_sha256", "captured_at", "entries_sha256", "collector_source_sha256", "collector_binary_sha256", "partial", "entries"])
def test_aux_provenance_and_bounds_are_enforced(tmp_path, settings, field):
    path, case, inventory, own, _, _, _ = combined(tmp_path, settings, metadata=True)
    body = unseal(path.read_text())
    aux = body["origins"][1]["aux_metadata"]
    aux[field] = False if field == "partial" else ([{}] if field == "entries" else "altered")
    path.write_text(seal(body))
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


def test_unknown_and_repeated_aux_names_remain_separate_unassociated_review_entries(tmp_path, settings):
    path, case, inventory, own, _, _, _ = combined(tmp_path, settings, metadata=True)
    body = unseal(path.read_text())
    aux = body["origins"][1]["aux_metadata"]
    entry = {"field_hex": b"unknown-subject-note".hex(), "value_hex": b"PRIVATE AUX VALUE".hex()}
    aux["entries"].extend([entry, entry.copy()])
    import json

    aux["entries_sha256"] = hashlib.sha256(json.dumps(aux["entries"], sort_keys=True).encode()).hexdigest()
    path.write_text(seal(body))
    result = read(settings, case, inventory, {own})
    rows = result["metadata_review"][0]["records"][-2:]
    assert all(row["recognized_field"] is None for row in rows)
    assert rows[0]["reference"] != rows[1]["reference"]
    assert "value_hex" not in str(result["metadata_review"])
    assert rows[0]["content_digest"] == rows[1]["content_digest"]
    assert "snapshot_metadata_scope_review" in result["pending"]
    assert "PRIVATE AUX VALUE" not in str(result["records"])
    aux["entries"][0]["field_hex"] = "00" * 4097
    aux["entries_sha256"] = hashlib.sha256(json.dumps(aux["entries"], sort_keys=True).encode()).hexdigest()
    path.write_text(seal(body))
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


@pytest.mark.parametrize("mutation", ["request", "inventory", "source_digest", "cutoff", "hash", "decoder", "partial", "duplicate", "duration", "pending"])
def test_combined_source_tampering_is_rejected(tmp_path, settings, mutation):
    path, case, inventory, own, _, _, _ = combined(tmp_path, settings)
    body = unseal(path.read_text())
    if mutation in {"request", "source_digest", "cutoff"}:
        body[mutation] = "altered"
    elif mutation == "inventory":
        body[mutation] = True
    elif mutation == "duplicate":
        duplicate = deepcopy(body["origins"][1])
        duplicate["decoder_observed_seconds"] += 1
        body["origins"].append(duplicate)
    else:
        origin = body["origins"][1]
        if mutation == "hash":
            origin["sha256"] = "0" * 64
        elif mutation == "decoder":
            origin["decoder"]["source_commit"] = "0" * 40
        elif mutation == "duration":
            origin["decoder_observed_seconds"] = True
        elif mutation == "pending":
            origin["pending"] = []
        else:
            origin["partial"] = False
    path.write_text(seal(body))
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


def test_native_crc_failure_rejects_source_and_removes_temporary_files(tmp_path, settings):
    _, _, inventory, own, _ = origins(tmp_path, settings)
    body, _ = capture(tmp_path / "native", inventory.created_at, [message(own)])
    raw = bytearray(base64.b64decode(body["content_base64"]))
    raw[-1] ^= 1
    body.update(content_base64=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest())
    decoder, digest = native_decoder()
    with pytest.raises(ValueError, match="decoder failed"):
        decode_body(body, decoder, decoder_sha256=digest)
    assert not list(Path("/tmp").glob("web-modelos-rdb-decode-*"))
    assert not Path("rdb-cli.log").exists()


def test_aux_wrapper_rejects_corrupt_crc_without_accepting_partial_stdout(tmp_path, settings):
    from scripts.collect_retained_rdb_aux import collect_aux

    _, _, inventory, own, _ = origins(tmp_path, settings)
    body, _ = capture(tmp_path / "native", inventory.created_at, [message(own)])
    decoder, digest = native_decoder()
    reconstructed = decode_body(body, decoder, decoder_sha256=digest)
    raw = bytearray(base64.b64decode(body["content_base64"]))
    raw[-1] ^= 1
    bad_hash = hashlib.sha256(raw).hexdigest()
    damaged = body | {"content_base64": base64.b64encode(raw).decode(), "sha256": bad_hash}
    aux, aux_hash = aux_decoder()
    with pytest.raises(ValueError, match="partial output is not accepted"):
        collect_aux(damaged, reconstructed | {"source_sha256": bad_hash}, aux, decoder_sha256=aux_hash)
    assert not list(Path("/tmp").glob("web-modelos-rdb-aux-*"))
