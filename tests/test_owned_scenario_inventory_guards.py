"""Reject foreign endpoints and unstable file observations without any services."""
from types import SimpleNamespace

import pytest

from scripts import owned_scenario_inventory as inventory


@pytest.mark.parametrize("host,port", [("remote.invalid", "34567"), ("", "34567"),
                                     ("127.0.0.1", "5432"), ("localhost", "34567")])
def test_database_endpoint_mismatch_is_rejected(monkeypatch, host, port):
    monkeypatch.setattr("django.db.connection", SimpleNamespace(settings_dict={
        "HOST": host, "PORT": port, "NAME": "test_promotion_gate_synthetic"}))
    metadata = {"NetworkSettings": {"Ports": {"5432/tcp": [
        {"HostIp": "127.0.0.1", "HostPort": "34567"}]}}}
    with pytest.raises(RuntimeError, match="database endpoint differs"):
        inventory.verify_database_endpoint(metadata)


@pytest.mark.parametrize("parent_link", [False, True])
def test_file_or_parent_symlink_is_not_read(tmp_path, monkeypatch, parent_link):
    root = tmp_path / "root"
    root.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "file").write_bytes(b"synthetic-not-in-declared-root")
    if parent_link:
        (root / "linked").symlink_to(elsewhere, target_is_directory=True)
        relative = "linked/file"
    else:
        (root / "file").symlink_to(elsewhere / "file")
        relative = "file"
    def forbidden(*args):
        raise AssertionError("Symlink target must never be read")
    monkeypatch.setattr(inventory.os, "read", forbidden)
    with pytest.raises(OSError):
        inventory.hash_regular_file(root, relative, 1024)


def test_file_change_during_hash_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "file"
    path.write_bytes(b"synthetic-own-before")
    original = inventory.os.read
    changed = False
    def mutate(descriptor, size):
        nonlocal changed
        result = original(descriptor, size)
        if result and not changed:
            changed = True
            with path.open("ab") as stream:
                stream.write(b"-altered")
        return result
    monkeypatch.setattr(inventory.os, "read", mutate)
    with pytest.raises(RuntimeError, match="changed during observation"):
        inventory.hash_regular_file(tmp_path, "file", 1024)


def test_file_budget_is_enforced_during_read(tmp_path):
    (tmp_path / "file").write_bytes(b"synthetic-over-budget")
    with pytest.raises(RuntimeError, match="inventory exceeded"):
        inventory.hash_regular_file(tmp_path, "file", 4)


def test_process_capture_drains_both_streams_and_rejects_overflow():
    import sys
    command = [sys.executable, "-c", "import os; os.write(1,b'own'); os.write(2,b'log')"]
    assert inventory.bounded_process_output(command, max_bytes=6) == {"stdout": b"own", "stderr": b"log"}
    with pytest.raises(RuntimeError, match="byte budget"):
        inventory.bounded_process_output(command, max_bytes=5)


def test_process_capture_rejects_timeout_and_nonzero_exit():
    import sys
    with pytest.raises(RuntimeError, match="timed out"):
        inventory.bounded_process_output([sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.05)
    with pytest.raises(RuntimeError, match="command failed"):
        inventory.bounded_process_output([sys.executable, "-c", "raise SystemExit(1)"])
