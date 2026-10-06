from copy import deepcopy
from uuid import uuid4

import pytest

from scripts.recovery_ledger import LedgerIntegrityError
from scripts.recovery_receipts import validate_receipt


def receipt():
    return {
        "schema": "recovery-execution-receipt-v1",
        "execution": str(uuid4()),
        "scope": "account",
        "subject": "12",
        "purposes": ["authentication"],
        "pending_purposes": ["evidence"],
        "references": {
            "schema": "recovery-resource-references-v1",
            "resources": {"tokens": [str(uuid4())], "recovery_codes": ["1"]},
            "account": {
                "id": "12",
                "minimum_session_version": 2,
                "minimum_mfa_version": 3,
                "anonymize": False,
            },
        },
    }


def test_valid_authentication_and_transient_only():
    value = receipt()
    assert validate_receipt(value) == value
    value["purposes"] = ["transient_copy"]
    value["references"].pop("account")
    value["references"]["resources"] = {"exports": [str(uuid4())]}
    assert validate_receipt(value) == value


@pytest.mark.parametrize(
    "damage",
    [
        "purpose",
        "binding",
        "epoch",
        "unknown",
        "duplicate",
        "unhashable",
        "unexpected_scope",
        "execution",
    ],
)
def test_invalid_receipts(damage):
    value = deepcopy(receipt())
    if damage == "purpose":
        value["purposes"] = ["publish_everyone"]
    elif damage == "binding":
        value["references"]["account"]["id"] = "99"
    elif damage == "epoch":
        value["references"]["account"]["minimum_session_version"] = True
    elif damage == "unknown":
        value["references"]["resources"]["third_party"] = ["1"]
    elif damage == "duplicate":
        value["references"]["resources"]["recovery_codes"] = ["1", "1"]
    elif damage == "unhashable":
        value["references"]["resources"]["tokens"] = [{}]
    elif damage == "unexpected_scope":
        value["scope"] = []
    else:
        value["execution"] = "1"
    with pytest.raises(LedgerIntegrityError):
        validate_receipt(value)


def media_receipt():
    value = receipt()
    value.update(
        scope="person", subject=str(uuid4()), purposes=["media"], pending_purposes=["media"]
    )
    value["references"] = {
        "schema": "recovery-resource-references-v1",
        "person": {
            "id": value["subject"],
            "minimum_rights_version": 2,
            "minimum_manager_version": 1,
        },
        "resources": {
            "photos": [{"photo": "1", "blob": str(uuid4()), "shared": True}],
            "media_operation": "detach_shared_and_review_exclusive",
        },
        "media_jobs": [],
    }
    return value


def test_partial_shared_media_is_valid():
    value = media_receipt()
    assert validate_receipt(value) == value


@pytest.mark.parametrize("path", ["../private", "/etc/private", "a/../b", "a\\b", "a\x00b"])
def test_unsafe_media_paths_are_rejected(path):
    value = media_receipt()
    value["pending_purposes"] = []
    value["references"]["resources"]["photos"][0]["shared"] = False
    value["references"]["resources"]["media_operation"] = "erase_exclusive"
    value["references"]["media_jobs"] = [
        {
            "job": "1",
            "blob": value["references"]["resources"]["photos"][0]["blob"],
            "paths": {"original": path, "derivative": ""},
        }
    ]
    with pytest.raises(LedgerIntegrityError):
        validate_receipt(value)


def test_shared_blob_never_has_physical_erasure_job():
    value = media_receipt()
    value["references"]["media_jobs"] = [
        {
            "job": "1",
            "blob": value["references"]["resources"]["photos"][0]["blob"],
            "paths": {"original": "originals/synthetic.webp", "derivative": ""},
        }
    ]
    with pytest.raises(LedgerIntegrityError):
        validate_receipt(value)
