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


@pytest.mark.parametrize("symlink", [False, True])
def test_private_archive_never_replaces_existing_destination(tmp_path, symlink):
    existing = tmp_path / "archive"
    original = tmp_path / "original"
    original.write_bytes(b"preserve")
    if symlink:
        existing.symlink_to(original)
    else:
        existing.write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        inventory.publish_private_archive(tmp_path, "archive", b"new")
    assert existing.read_bytes() == b"preserve"
    assert not list(tmp_path.glob(".private-*"))


def test_private_archive_rejects_redirected_parent(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    with pytest.raises(OSError):
        inventory.publish_private_archive(linked, "archive", b"new")
    assert not list(actual.iterdir())


def test_private_archive_publication_failure_removes_temporary(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("synthetic publication failure")
    monkeypatch.setattr(inventory.os, "link", fail)
    with pytest.raises(OSError, match="synthetic publication"):
        inventory.publish_private_archive(tmp_path, "archive", b"new")
    assert not list(tmp_path.iterdir())


def test_private_content_uses_the_same_bounded_descriptor_as_its_hash(tmp_path):
    import hashlib

    private = b"synthetic-capability\x00not-for-public-observation"
    (tmp_path / "private").write_bytes(private)
    size, digest, original = inventory.hash_regular_file(
        tmp_path, "private", len(private), include_content=True
    )
    assert size == len(private)
    assert digest == hashlib.sha256(private).hexdigest()
    assert original == private
    assert inventory.hash_regular_file(tmp_path, "private", len(private)) == (size, digest)
    with pytest.raises(RuntimeError, match="inventory exceeded"):
        inventory.hash_regular_file(tmp_path, "private", len(private) - 1, include_content=True)


@pytest.mark.parametrize("unchanged_metadata", [False, True])
def test_private_content_rejects_post_read_mutation(tmp_path, monkeypatch, unchanged_metadata):
    target = tmp_path / "private"
    target.write_bytes(b"synthetic-original")
    if unchanged_metadata:
        observed = target.stat()
        monkeypatch.setattr(inventory.os, "fstat", lambda descriptor: observed)
    read = inventory.os.read
    changed = False

    def mutate(descriptor, count):
        nonlocal changed
        content = read(descriptor, count)
        if content and not changed:
            changed = True
            target.write_bytes(b"synthetic-altered!")
        return content

    monkeypatch.setattr(inventory.os, "read", mutate)
    with pytest.raises(RuntimeError, match="changed during observation"):
        inventory.hash_regular_file(tmp_path, "private", 1024, include_content=True)
