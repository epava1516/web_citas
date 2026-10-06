import copy
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from scripts.recovery_ledger import ZERO, Checkpoint, LedgerIntegrityError, RecoveryLedger


def chain():
    codec = RecoveryLedger(Fernet.generate_key(), b"s" * 32)
    start = Checkpoint(str(uuid4()), 0, ZERO)
    first, middle = codec.append(start, str(uuid4()), {"operation": "synthetic-withdrawal"})
    second, end = codec.append(middle, str(uuid4()), {"operation": "synthetic-erasure"})
    return codec, start, middle, end, [first, second]


def test_roundtrip_and_suffix():
    codec, start, middle, end, records = chain()
    assert codec.verify(records, start, end) == [
        {"operation": "synthetic-withdrawal"},
        {"operation": "synthetic-erasure"},
    ]
    assert codec.verify(records[1:], middle, end) == [{"operation": "synthetic-erasure"}]
    assert codec.verify([], end, end) == []
    assert "synthetic-erasure" not in str(records)


@pytest.mark.parametrize(
    "mutation",
    [
        "body",
        "signature",
        "sequence",
        "previous",
        "omit",
        "truncate",
        "reorder",
        "duplicate",
        "unknown",
    ],
)
def test_alterations_fail(mutation):
    codec, start, middle, end, records = chain()
    records = copy.deepcopy(records)
    if mutation in {"body", "signature", "previous"}:
        records[0][mutation] = "x"
    elif mutation == "sequence":
        records[0]["sequence"] = True
    elif mutation == "unknown":
        records[0]["extra"] = "x"
    elif mutation == "omit":
        records.pop(0)
    elif mutation == "truncate":
        records.pop()
    elif mutation == "reorder":
        records.reverse()
    else:
        records.append(records[0])
    with pytest.raises(LedgerIntegrityError):
        codec.verify(records, start, end)


def test_checkpoint_and_keys_fail():
    codec, start, middle, end, records = chain()
    with pytest.raises(LedgerIntegrityError):
        codec.verify(records, end, start)
    with pytest.raises(LedgerIntegrityError):
        codec.verify(records, start, Checkpoint(str(uuid4()), end.sequence, end.head))
    with pytest.raises(LedgerIntegrityError):
        RecoveryLedger(Fernet.generate_key(), b"t" * 32).verify(records, start, end)
    with pytest.raises(LedgerIntegrityError):
        RecoveryLedger(Fernet.generate_key(), b"s" * 32).verify(records, start, end)


def test_no_decryption_before_full_checkpoint_verification(monkeypatch):
    codec, start, middle, end, records = chain()

    def forbidden_decrypt(*args, **kwargs):
        raise AssertionError("Decryption preceded integrity verification")

    monkeypatch.setattr(codec.cipher, "decrypt", forbidden_decrypt)
    with pytest.raises(LedgerIntegrityError):
        codec.verify(records[:1], start, end)


def test_encoded_and_decoded_same_key_rejected():
    import base64

    key = Fernet.generate_key()
    with pytest.raises(ValueError):
        RecoveryLedger(key, key)
    with pytest.raises(ValueError):
        RecoveryLedger(key, base64.urlsafe_b64decode(key))


@pytest.mark.parametrize(
    "mutation", ["duplicate_event", "boolean_sequence", "boolean_schema", "wrong_previous"]
)
def test_signed_malformed_records_fail(mutation):
    from scripts.recovery_ledger import digest

    codec, start, middle, end, records = chain()
    if mutation == "duplicate_event":
        records[1]["event"] = records[0]["event"]
    elif mutation == "boolean_sequence":
        records[1]["sequence"] = True
    elif mutation == "boolean_schema":
        records[1]["schema"] = True
    else:
        records[1]["previous"] = ZERO
    unsigned = {k: v for k, v in records[1].items() if k != "signature"}
    records[1]["signature"] = codec.signature(unsigned)
    expected = Checkpoint(end.ledger, end.sequence, digest(records[1]))
    with pytest.raises(LedgerIntegrityError):
        codec.verify(records, start, expected)


def test_total_bundle_limit(monkeypatch):
    import scripts.recovery_ledger as module

    codec, start, middle, end, records = chain()
    monkeypatch.setattr(module, "MAX_BUNDLE_BYTES", len(module.canonical(records[0])))
    with pytest.raises(LedgerIntegrityError):
        codec.verify(records, start, end)
