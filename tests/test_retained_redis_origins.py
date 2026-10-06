"""Combined sources stay partial, scoped, and explicit about reconstruction."""

import base64
import hashlib
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from retained_rdb_fixture import capture, native_decoder
from test_redis_history_scope import message
from test_scoped_redis_history_origins import origins, read

from apps.safety.crypto import seal, unseal
from scripts.decode_retained_rdb_origin import decode_body
from scripts.scope_retained_redis_origin import prepare_origins


def combined(tmp_path, settings):
    source, case, inventory, own, other = origins(tmp_path, settings)
    body, expiration = capture(tmp_path / "native", inventory.created_at, [message(own), message(other)])
    snapshot = tmp_path / "snapshot.encrypted"
    snapshot.write_text(seal(body))
    snapshot.chmod(0o600)
    decoder, digest = native_decoder()
    path = prepare_origins([source, snapshot], tmp_path, inventory, decoder=decoder, decoder_sha256=digest)
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
