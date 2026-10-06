"""Real native captures and PostgreSQL/HTTP gates for opaque physical metadata."""

import base64
import hashlib
import json
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from retained_rdb_fixture import metadata_decoder, native_decoder
from test_retained_redis_origins import combined
from test_scoped_redis_history_origins import read

from apps.safety.crypto import seal, unseal
from scripts.collect_retained_rdb_metadata import collect_physical
from scripts.decode_retained_rdb_origin import decode_body


def test_native_census_preserves_expired_key_attributes_without_exposing_global_keys(tmp_path, settings):
    path, case, inventory, own, other, source, expiration = combined(tmp_path, settings, metadata="physical")
    metadata = unseal(path.read_text())["origins"][1]["physical_metadata"]
    assert metadata["source_bytes"] == len(base64.b64decode(source["content_base64"]))
    key = next(row for row in metadata["events"] if row["event"] == "key")
    assert key["key_hex"] == b"fixture:q".hex() and key["expiry"] == expiration
    result = read(settings, case, inventory, {own})
    review = result["metadata_review"][0]
    assert review["physical_summary"]["consumed_bytes"] == metadata["source_bytes"]
    assert review["physical_summary"]["event_counts"]["key"] == 1
    assert review["physical_summary"]["additional_formats_pending"] == []
    assert review["physical_records"] and review["records"]
    assert review["decision"] == "pending_independent_review"
    assert all(row["association"] == "infrastructure_scope_unreviewed" for row in review["physical_records"])
    for private in ["key_hex", "field_hex", "value_hex", "fixture:q", b"fixture:q".hex(), own, other]:
        assert private not in str(review)
    assert len(result["records"]) == 2 and result["partial"]
    assert "snapshot_metadata_scope_review" in result["pending"]
    assert not list(Path("/tmp").glob("web-modelos-rdb-physical-*"))


@pytest.mark.parametrize("mutation", ["source", "cut", "collector", "hash", "trailer", "header", "context", "limit", "boolean", "unknown", "duplicate"])
def test_rehashed_census_cannot_bypass_provenance_protocol_or_bounds(tmp_path, settings, mutation):
    path, case, inventory, own, _, _, _ = combined(tmp_path, settings, metadata="physical")
    body = unseal(path.read_text())
    metadata = body["origins"][1]["physical_metadata"]
    key = next(row for row in metadata["events"] if row["event"] == "key")
    if mutation == "source":
        metadata["source_sha256"] = "0" * 64
    elif mutation == "cut":
        metadata["captured_at"] = "altered"
    elif mutation == "collector":
        metadata["collector_source_sha256"] = "0" * 64
    elif mutation == "hash":
        metadata["collector_binary_sha256"] = "altered"
    elif mutation == "trailer":
        metadata["events"][-1]["source_bytes"] += 1
    elif mutation == "header":
        metadata["events"].insert(1, metadata["events"][0].copy())
    elif mutation == "context":
        key["database"] += 1
    elif mutation == "limit":
        key["key_hex"] = "00" * 4097
    elif mutation == "boolean":
        key["expiry"] = True
    elif mutation == "unknown":
        metadata["events"].insert(-1, {"event": "ignored-new-format"})
    elif mutation == "duplicate":
        metadata["events"].insert(-1, key.copy())
    metadata["events_sha256"] = hashlib.sha256(json.dumps(metadata["events"], sort_keys=True).encode()).hexdigest()
    path.write_text(seal(body))
    with pytest.raises(ValidationError):
        read(settings, case, inventory, {own})


@pytest.mark.parametrize("damage", ["crc", "trailing_bytes", "binary_hash", "writable_binary"])
def test_native_rejects_physical_corruption_and_cleans_private_files(tmp_path, settings, damage):
    _, _, _, _, _, body, _ = combined(tmp_path, settings)
    decoder, decoder_hash = native_decoder()
    reconstruction = decode_body(body, decoder, decoder_sha256=decoder_hash)
    collector, collector_hash = metadata_decoder()
    if damage in {"crc", "trailing_bytes"}:
        raw = bytearray(base64.b64decode(body["content_base64"]))
        if damage == "crc":
            raw[-1] ^= 1
        else:
            raw.extend(b"unexamined-data")
        changed_hash = hashlib.sha256(raw).hexdigest()
        body = body | {"content_base64": base64.b64encode(raw).decode(), "sha256": changed_hash}
        reconstruction = reconstruction | {"source_sha256": changed_hash}
    elif damage == "binary_hash":
        collector_hash = "0" * 64
    else:
        copied = tmp_path / "collector"
        copied.write_bytes(collector.read_bytes())
        copied.chmod(0o777)
        collector = copied
    with pytest.raises(ValueError):
        collect_physical(body, reconstruction, collector, decoder_sha256=collector_hash)
    assert not list(Path("/tmp").glob("web-modelos-rdb-physical-*"))
