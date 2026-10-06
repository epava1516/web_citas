import hashlib
import json
from pathlib import Path

import pytest

from scripts import inventory_retained_origins as inventory


def capture_declaration(path):
    from scripts.collect_access_resource_logs import SERVICES

    return {
        "encrypted_artifact": str(path),
        "captured_at": "2026-10-06T12:00:00+00:00",
        "services": [
            {"service": service, "stdout_bytes": 1, "stderr_bytes": 0} for service in SERVICES
        ],
    }


def test_inventory_streams_exact_ciphertext_and_preserves_source(tmp_path):
    path = tmp_path / "origin.encrypted"
    body = b"opaque-synthetic-ciphertext" * 10000
    path.write_bytes(body)
    path.chmod(0o600)
    result = inventory.inspect_origin(path)
    assert result["bytes"] == len(body)
    assert result["sha256"] == hashlib.sha256(body).hexdigest()
    assert path.read_bytes() == body


def test_inventory_rejects_symlinks_permissions_and_oversized_sources(tmp_path, monkeypatch):
    path = tmp_path / "origin.encrypted"
    path.write_bytes(b"opaque")
    path.chmod(0o600)
    link = tmp_path / "link.encrypted"
    link.symlink_to(path)
    with pytest.raises(OSError):
        inventory.inspect_origin(link)
    path.chmod(0o644)
    with pytest.raises(ValueError, match="Unsafe"):
        inventory.inspect_origin(path)
    path.chmod(0o600)
    monkeypatch.setattr(inventory, "MAX_BYTES", 3)
    with pytest.raises(ValueError, match="oversized"):
        inventory.inspect_origin(path)


def test_declared_log_census_binds_acta_and_counts_duplicate_references_once(tmp_path):
    origin = tmp_path / "origin.encrypted"
    origin.write_bytes(b"opaque-synthetic-original")
    origin.chmod(0o600)
    declaration = capture_declaration(origin)
    evidence = tmp_path / "acta.json"
    evidence.write_text(json.dumps({"captures": [declaration, declaration]}))
    result = inventory.inventory_log_captures([evidence])
    assert result["unique_origins"] == 1
    assert result["capture_references"] == 2
    assert result["declared_sources_inventoried"] is True
    row = result["origins"][0]
    assert row["sha256"] == hashlib.sha256(origin.read_bytes()).hexdigest()
    assert row["declarations"][1]["pointer"] == "/captures/1"
    assert (
        row["declarations"][0]["evidence_sha256"]
        == hashlib.sha256(evidence.read_bytes()).hexdigest()
    )
    assert result["partial"] is True
    assert result["subject_association_verified"] is False
    assert "opaque-synthetic-original" not in str(result)


def test_declared_census_preserves_missing_unsafe_and_conflicting_sources(tmp_path):
    unsafe = tmp_path / "unsafe.encrypted"
    unsafe.write_bytes(b"synthetic")
    unsafe.chmod(0o644)
    safe = tmp_path / "safe.encrypted"
    safe.write_bytes(b"synthetic")
    safe.chmod(0o600)
    altered = capture_declaration(safe) | {"captured_at": "2026-10-06T13:00:00+00:00"}
    evidence = tmp_path / "acta.json"
    evidence.write_text(
        json.dumps(
            [
                capture_declaration(tmp_path / "missing.encrypted"),
                capture_declaration(unsafe),
                capture_declaration(safe),
                altered,
            ]
        )
    )
    result = inventory.inventory_log_captures([evidence])
    rows = {Path(row["path"]).name: row for row in result["origins"]}
    assert rows["missing.encrypted"]["status"] == "missing"
    assert rows["unsafe.encrypted"]["status"] == "unreadable_or_unsafe"
    assert rows["safe.encrypted"]["pending"] == ["conflicting_capture_declarations"]
    assert result["declared_sources_inventoried"] is False


@pytest.mark.parametrize(
    "change", ["content", "naive_cutoff", "relative_path", "duplicate_service"]
)
def test_capture_metadata_does_not_admit_content_or_ambiguous_declarations(tmp_path, change):
    declaration = capture_declaration(tmp_path / "origin.encrypted")
    if change == "content":
        declaration["services"][0]["stdout"] = "private-content-must-not-enter-report"
    elif change == "naive_cutoff":
        declaration["captured_at"] = "2026-10-06T12:00:00"
    elif change == "relative_path":
        declaration["encrypted_artifact"] = "relative.encrypted"
    else:
        declaration["services"][1] = declaration["services"][0]
    evidence = tmp_path / "acta.json"
    evidence.write_text(json.dumps(declaration))
    with pytest.raises(ValueError):
        inventory.inventory_log_captures([evidence])
