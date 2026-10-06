import hashlib

import pytest

from scripts import inventory_retained_origins as inventory


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
