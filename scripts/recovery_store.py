"""Private durable local ledger adapter; not off-host backup infrastructure."""

import fcntl
import hashlib
import hmac
import json
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from .recovery_ledger import (
    MAX_BUNDLE_BYTES,
    MAX_EVENTS,
    MAX_RECORD_BYTES,
    Checkpoint,
    LedgerIntegrityError,
    canonical,
    digest,
)


class RecoveryStore:
    def __init__(self, records_directory, checkpoint_directory, codec, *, expected_checkpoint=None):
        self.codec = codec
        if expected_checkpoint is not None and not isinstance(expected_checkpoint, Checkpoint):
            raise ValueError("Typed independent checkpoint required")
        self.expected_checkpoint = expected_checkpoint
        self.records_directory = Path(records_directory)
        self.checkpoint_directory = Path(checkpoint_directory)
        if self.records_directory.resolve() == self.checkpoint_directory.resolve():
            raise ValueError("Separate checkpoint directory required")
        for directory in [self.records_directory, self.checkpoint_directory]:
            metadata = directory.lstat()
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o077:
                raise ValueError("Existing private directory required")

    @contextmanager
    def _locked(self):
        directory = os.open(self.checkpoint_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            lock = os.open(".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                metadata = os.fstat(lock)
                if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o077:
                    raise LedgerIntegrityError("Unsafe checkpoint lock")
                fcntl.flock(lock, fcntl.LOCK_EX)
                yield
            finally:
                os.close(lock)
        finally:
            os.close(directory)

    def _read(self, directory, name):
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptor)
            except FileNotFoundError:
                return None
            with os.fdopen(fd, "rb") as source:
                metadata = os.fstat(source.fileno())
                if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o077:
                    raise LedgerIntegrityError("Unsafe recovery artifact")
                data = source.read(MAX_RECORD_BYTES + 1)
                if len(data) > MAX_RECORD_BYTES:
                    raise LedgerIntegrityError("Recovery artifact too large")
                return json.loads(data)
        finally:
            os.close(descriptor)

    def _write(self, directory, name, value, replace=False):
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        temporary = ".pending-" + str(uuid4())
        try:
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=descriptor,
            )
            with os.fdopen(fd, "wb") as target:
                target.write(canonical(value))
                target.flush()
                os.fsync(target.fileno())
            if replace:
                os.replace(temporary, name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
            else:
                try:
                    os.link(
                        temporary,
                        name,
                        src_dir_fd=descriptor,
                        dst_dir_fd=descriptor,
                        follow_symlinks=False,
                    )
                except FileExistsError:
                    if self._read(directory, name) != value:
                        raise LedgerIntegrityError("Conflicting durable record")
            os.fsync(descriptor)
        finally:
            try:
                os.unlink(temporary, dir_fd=descriptor)
            except FileNotFoundError:
                pass
            os.close(descriptor)

    def _checkpoint_signature(self, value):
        return hmac.new(
            self.codec.signing_key, b"recovery-checkpoint-v1\0" + canonical(value), hashlib.sha256
        ).hexdigest()

    def checkpoint(self):
        value = self._read(self.checkpoint_directory, "checkpoint.json")
        if value is None:
            raise LedgerIntegrityError("Independent checkpoint missing")
        if not isinstance(value, dict) or set(value) != {
            "schema",
            "ledger",
            "sequence",
            "head",
            "signature",
        }:
            raise LedgerIntegrityError("Malformed checkpoint")
        unsigned = {key: item for key, item in value.items() if key != "signature"}
        if (
            type(value["schema"]) is not int
            or value["schema"] != 1
            or not isinstance(value["signature"], str)
            or not hmac.compare_digest(self._checkpoint_signature(unsigned), value["signature"])
        ):
            raise LedgerIntegrityError("Checkpoint signature invalid")
        return Checkpoint(value["ledger"], value["sequence"], value["head"])

    def initialize(self, genesis):
        with self._locked():
            return self._initialize(genesis)

    def _initialize(self, genesis):
        if genesis.sequence != 0:
            raise LedgerIntegrityError("Initialization requires genesis")
        value = dict(schema=1, ledger=genesis.ledger, sequence=genesis.sequence, head=genesis.head)
        value["signature"] = self._checkpoint_signature(value)
        self._write(self.checkpoint_directory, "checkpoint.json", value)
        return self.checkpoint()

    def append(self, record):
        with self._locked():
            return self._append(record)

    def _append(self, record):
        current = self.checkpoint()
        target = Checkpoint(record["ledger"], record["sequence"], digest(record))
        filename = f"{target.sequence:020d}.json"
        if current == target:
            if self._read(self.records_directory, filename) != record:
                raise LedgerIntegrityError("Checkpoint record missing or altered")
            return current
        self.codec.verify([record], current, target)
        self._write(self.records_directory, filename, record)
        value = dict(schema=1, ledger=target.ledger, sequence=target.sequence, head=target.head)
        value["signature"] = self._checkpoint_signature(value)
        self._write(self.checkpoint_directory, "checkpoint.json", value, replace=True)
        return self.checkpoint()

    def confirm(self, record):
        """Confirm an older durable record after a rolled-back DB acknowledgement."""
        with self._locked():
            current = self.checkpoint()
            if record["ledger"] != current.ledger or record["sequence"] > current.sequence:
                raise LedgerIntegrityError("Record not checkpointed")
            filename = f"{record['sequence']:020d}.json"
            if self._read(self.records_directory, filename) != record:
                raise LedgerIntegrityError("Durable record mismatch")
            start = Checkpoint(current.ledger, record["sequence"] - 1, record["previous"])
            self._recover(start)
            return current

    def recover(self, start):
        with self._locked():
            return self._recover(start)

    def _recover(self, start):
        expected = self.checkpoint()
        if self.expected_checkpoint is not None and expected != self.expected_checkpoint:
            raise LedgerIntegrityError("Recovery checkpoint differs from independent authority")
        if start.ledger != expected.ledger or start.sequence > expected.sequence:
            raise LedgerIntegrityError("Checkpoint rollback or ledger mismatch")
        if expected.sequence - start.sequence > MAX_EVENTS:
            raise LedgerIntegrityError("Recovery suffix too large")
        records, total_bytes = [], 0
        for sequence in range(start.sequence + 1, expected.sequence + 1):
            record = self._read(self.records_directory, f"{sequence:020d}.json")
            total_bytes += len(canonical(record))
            if total_bytes > MAX_BUNDLE_BYTES:
                raise LedgerIntegrityError("Recovery bundle too large")
            records.append(record)
        return self.codec.verify(records, start, expected)
