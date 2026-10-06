"""Encrypted recovery chain. Trusted checkpoints must come from outside the backup.

This codec does not authorize events, export an outbox, or apply recovery effects.
Persist encoded records: retries must reuse ciphertext rather than re-encrypt it.
"""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken

ZERO = "0" * 64
MAX_RECORD_BYTES = 65536
MAX_EVENTS = 10000
MAX_BUNDLE_BYTES = 16 * 1024 * 1024


class LedgerIntegrityError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def valid_hash(value):
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


@dataclass(frozen=True)
class Checkpoint:
    ledger: str
    sequence: int
    head: str

    def __post_init__(self):
        try:
            if str(UUID(self.ledger)) != self.ledger:
                raise ValueError
            if type(self.sequence) is not int or self.sequence < 0 or not valid_hash(self.head):
                raise ValueError
            if self.sequence == 0 and self.head != ZERO:
                raise ValueError
        except (TypeError, ValueError, AttributeError) as exc:
            raise LedgerIntegrityError("Invalid checkpoint") from exc


class RecoveryLedger:
    def __init__(self, encryption_key, signing_key):
        if (
            not isinstance(signing_key, bytes)
            or len(signing_key) < 32
            or signing_key == encryption_key
        ):
            raise ValueError("Separate signing key of at least 32 bytes required")
        self.cipher = Fernet(encryption_key)
        if hmac.compare_digest(signing_key, base64.urlsafe_b64decode(encryption_key)):
            raise ValueError("Encryption and signing keys must be independent")
        self.signing_key = signing_key

    def signature(self, record):
        return hmac.new(self.signing_key, canonical(record), hashlib.sha256).hexdigest()

    def append(self, checkpoint, event_id, payload):
        if not isinstance(payload, dict) or str(UUID(event_id)) != event_id:
            raise ValueError("Canonical event UUID and object payload required")
        body = canonical(payload)
        if len(body) > MAX_RECORD_BYTES // 2:
            raise ValueError("Payload too large")
        record = dict(
            schema=1,
            ledger=checkpoint.ledger,
            sequence=checkpoint.sequence + 1,
            event=event_id,
            previous=checkpoint.head,
            body=self.cipher.encrypt(body).decode("ascii"),
        )
        record["signature"] = self.signature(record)
        return record, Checkpoint(checkpoint.ledger, record["sequence"], digest(record))

    def verify(self, records, start, expected):
        """Verify the entire suffix before decrypting; never yield partial recovery data."""
        if not isinstance(records, list) or len(records) > MAX_EVENTS:
            raise LedgerIntegrityError("Invalid event bundle")
        if start.ledger != expected.ledger or expected.sequence < start.sequence:
            raise LedgerIntegrityError("Checkpoint rollback or ledger mismatch")
        current, seen = start, set()
        total_bytes = 0
        try:
            for record in records:
                if not isinstance(record, dict) or set(record) != {
                    "schema",
                    "ledger",
                    "sequence",
                    "event",
                    "previous",
                    "body",
                    "signature",
                }:
                    raise ValueError
                record_bytes = canonical(record)
                total_bytes += len(record_bytes)
                if len(record_bytes) > MAX_RECORD_BYTES or total_bytes > MAX_BUNDLE_BYTES:
                    raise ValueError
                unsigned = {k: v for k, v in record.items() if k != "signature"}
                if not valid_hash(record["signature"]) or not hmac.compare_digest(
                    self.signature(unsigned), record["signature"]
                ):
                    raise ValueError
                if type(record["schema"]) is not int or record["schema"] != 1:
                    raise ValueError
                if (
                    type(record["sequence"]) is not int
                    or record["sequence"] != current.sequence + 1
                ):
                    raise ValueError
                if record["ledger"] != current.ledger or record["previous"] != current.head:
                    raise ValueError
                if str(UUID(record["event"])) != record["event"] or record["event"] in seen:
                    raise ValueError
                if not isinstance(record["body"], str):
                    raise ValueError
                seen.add(record["event"])
                current = Checkpoint(current.ledger, record["sequence"], digest(record))
            if current != expected:
                raise ValueError
            payloads = []
            for record in records:
                plaintext = self.cipher.decrypt(record["body"].encode("ascii"))
                payload = json.loads(plaintext)
                if not isinstance(payload, dict) or canonical(payload) != plaintext:
                    raise ValueError
                payloads.append(payload)
            return payloads
        except (ValueError, TypeError, KeyError, AttributeError, InvalidToken, UnicodeError) as exc:
            raise LedgerIntegrityError("Recovery chain verification failed") from exc
