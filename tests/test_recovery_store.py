import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from scripts.recovery_ledger import ZERO, Checkpoint, LedgerIntegrityError, RecoveryLedger
from scripts.recovery_store import RecoveryStore


def fixture(tmp_path):
    records, checkpoints = tmp_path / "records", tmp_path / "authority"
    records.mkdir(mode=0o700)
    checkpoints.mkdir(mode=0o700)
    codec = RecoveryLedger(Fernet.generate_key(), b"r" * 32)
    store = RecoveryStore(records, checkpoints, codec)
    start = Checkpoint(str(uuid4()), 0, ZERO)
    store.initialize(start)
    record, end = codec.append(start, str(uuid4()), {"synthetic": "erasure"})
    return store, start, record, end


def test_durable_roundtrip_reopen_and_concurrent_replay(tmp_path):
    store, start, record, end = fixture(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(store.append, [record, record]))
    assert results == [end, end]
    reopened = RecoveryStore(store.records_directory, store.checkpoint_directory, store.codec)
    assert reopened.recover(start) == [{"synthetic": "erasure"}]
    assert reopened.append(record) == end
    for path in [
        store.records_directory / "00000000000000000001.json",
        store.checkpoint_directory / "checkpoint.json",
    ]:
        assert path.stat().st_mode & 0o077 == 0
        assert "erasure" not in path.read_text()


def test_crash_between_record_and_checkpoint_recovers_by_exact_retry(tmp_path, monkeypatch):
    store, start, record, end = fixture(tmp_path)
    original = store._write

    def fail(directory, name, value, replace=False):
        if name == "checkpoint.json":
            raise OSError("Synthetic checkpoint write failure")
        return original(directory, name, value, replace)

    with monkeypatch.context() as patch:
        patch.setattr(store, "_write", fail)
        with pytest.raises(OSError):
            store.append(record)
    assert store.checkpoint() == start
    assert store.append(record) == end
    assert store.recover(start) == [{"synthetic": "erasure"}]


@pytest.mark.parametrize("damage", ["missing_record", "record", "checkpoint", "missing_checkpoint"])
def test_recovery_refuses_missing_or_altered_artifacts(tmp_path, damage):
    store, start, record, end = fixture(tmp_path)
    store.append(record)
    path = store.records_directory / "00000000000000000001.json"
    if damage == "missing_record":
        path.unlink()
    elif damage == "record":
        value = json.loads(path.read_text())
        value["body"] = "tampered"
        path.write_text(json.dumps(value))
    elif damage == "missing_checkpoint":
        (store.checkpoint_directory / "checkpoint.json").unlink()
    else:
        path = store.checkpoint_directory / "checkpoint.json"
        value = json.loads(path.read_text())
        value["sequence"] = 0
        path.write_text(json.dumps(value))
    with pytest.raises(LedgerIntegrityError):
        store.recover(start)


def test_private_directories_and_symlink_guard(tmp_path):
    store, start, record, end = fixture(tmp_path)
    with pytest.raises(ValueError):
        RecoveryStore(store.records_directory, store.records_directory, store.codec)
    store.records_directory.chmod(0o755)
    with pytest.raises(ValueError):
        RecoveryStore(store.records_directory, store.checkpoint_directory, store.codec)
    store.records_directory.chmod(0o700)
    external = tmp_path / "untouched"
    external.write_text("synthetic external file")
    (store.records_directory / "00000000000000000001.json").symlink_to(external)
    with pytest.raises(OSError):
        store.append(record)
    assert external.read_text() == "synthetic external file"
    assert store.checkpoint() == start


def test_recovery_bounds_memory_before_loading_full_suffix(tmp_path, monkeypatch):
    import scripts.recovery_store as module

    store, start, record, end = fixture(tmp_path)
    store.append(record)
    monkeypatch.setattr(module, "MAX_BUNDLE_BYTES", 1)
    with pytest.raises(LedgerIntegrityError):
        store.recover(start)


def test_independent_checkpoint_rejects_valid_signed_rollback(tmp_path):
    store, start, record, end = fixture(tmp_path)
    checkpoint_path = store.checkpoint_directory / "checkpoint.json"
    previous_signed_checkpoint = checkpoint_path.read_bytes()
    store.append(record)
    anchored = RecoveryStore(
        store.records_directory, store.checkpoint_directory, store.codec, expected_checkpoint=end
    )
    assert anchored.recover(start) == [{"synthetic": "erasure"}]
    # Both signatures are genuine: an independent anchor must reject the old one.
    checkpoint_path.write_bytes(previous_signed_checkpoint)
    checkpoint_path.chmod(0o600)
    assert store.recover(start) == []
    with pytest.raises(LedgerIntegrityError):
        anchored.recover(start)


@pytest.mark.parametrize("difference", ["ledger", "head", "sequence"])
def test_independent_checkpoint_requires_exact_identity(tmp_path, difference):
    store, start, record, end = fixture(tmp_path)
    store.append(record)
    expected = Checkpoint(
        str(uuid4()) if difference == "ledger" else end.ledger,
        end.sequence + 1 if difference == "sequence" else end.sequence,
        "a" * 64 if difference == "head" else end.head,
    )
    anchored = RecoveryStore(
        store.records_directory,
        store.checkpoint_directory,
        store.codec,
        expected_checkpoint=expected,
    )
    with pytest.raises(LedgerIntegrityError):
        anchored.recover(start)
