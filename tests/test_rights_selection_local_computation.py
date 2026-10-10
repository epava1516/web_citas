"""Local pure reuse preserves current signatures and late transaction rejection."""

from copy import deepcopy
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_batch_projection import REASON
from test_rights_portability_batch_projection import prepared as prepared_batch
from test_rights_portability_image_read_bulk import duplicate, prepared

from apps.safety import rights_portability_coverage_batch as batch
from apps.safety import rights_portability_image_read as image_reads
from apps.safety import rights_portability_selection_review as selection_review
from apps.safety import rights_portability_selection_store as selection_store
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsAction,
    RightsPortabilityCoverageRead,
    RightsPortabilitySelectionRead,
)

pytestmark = pytest.mark.django_db(transaction=True)


def many(request, settings, monkeypatch):
    case, selection, actor, decisions, first = prepared(request, settings, monkeypatch)
    rows = [first] + [duplicate(first, case, another_photo=True) for _ in range(15)]
    decisions = [dict(decisions[0], photo=str(row.photo_id)) for row in rows]
    return case, selection, actor, decisions, first, rows


def test_ciphertext_digest_once_per_call_but_all_reads_checked(request, settings, monkeypatch):
    case, selection, actor, decisions, first, _ = many(request, settings, monkeypatch)
    cipher_calls, validation_calls = [], []
    original_image_fingerprint = image_reads.fingerprint
    original_selection_fingerprint = selection_review.fingerprint
    original_validate = image_reads.validate_evidence

    def image_fingerprint(value):
        if value == selection.encrypted_selection:
            cipher_calls.append(value)
        return original_image_fingerprint(value)

    def selection_fingerprint(value):
        if value == selection.encrypted_selection:
            cipher_calls.append(value)
        return original_selection_fingerprint(value)

    def validate(*args, **kwargs):
        validation_calls.append(args[0].pk)
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(image_reads, "fingerprint", image_fingerprint)
    monkeypatch.setattr(selection_review, "fingerprint", selection_fingerprint)
    monkeypatch.setattr(image_reads, "validate_evidence", validate)
    with transaction.atomic():
        for _ in range(4):
            assert (
                len(image_reads.required_reads(selection, case, first.proof, decisions, actor))
                == 16
            )
    assert len(cipher_calls) == 4
    assert len(validation_calls) == 64


@pytest.mark.parametrize("change", ["ciphertext", "key"])
@pytest.mark.parametrize("last", [False, True])
def test_change_during_image_validation_rejects_even_last_image(
    request, settings, monkeypatch, change, last
):
    case, selection, actor, decisions, first, _ = many(request, settings, monkeypatch)
    original = image_reads.validate_evidence
    calls = 0

    def mutate(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == (16 if last else 2):
            if change == "ciphertext":
                selection.encrypted_selection += "changed"
            else:
                settings.SECRET_KEY += "changed"
        return result

    monkeypatch.setattr(image_reads, "validate_evidence", mutate)
    with transaction.atomic(), pytest.raises(ValidationError, match="ciphertext or signing key"):
        image_reads.required_reads(selection, case, first.proof, decisions, actor)


@pytest.mark.parametrize("change", ["image_signature", "selection_signature", "selection_reason"])
def test_last_evidence_still_rejects(request, settings, monkeypatch, change):
    case, selection, actor, decisions, first, rows = many(request, settings, monkeypatch)
    last = rows[-1]
    if change == "image_signature":
        RightsAction.objects.filter(pk=last.action_id).update(payload_digest="0" * 64)
    else:
        original = image_reads.validate_evidence
        calls = []

        def corrupt_last(evidence, *args, **kwargs):
            calls.append(evidence.pk)
            if len(calls) == 16:
                fields = (
                    {"payload_digest": "0" * 64}
                    if change == "selection_signature"
                    else {"encrypted_reason": "broken"}
                )
                RightsAction.objects.filter(pk=evidence.action_id).update(**fields)
                evidence.action.refresh_from_db()
            return original(evidence, *args, **kwargs)

        monkeypatch.setattr(image_reads, "validate_evidence", corrupt_last)
    with transaction.atomic(), pytest.raises(ValidationError):
        image_reads.required_reads(selection, case, first.proof, decisions, actor)
    if change != "image_signature":
        assert len(calls) == 16


def test_third_child_ciphertext_change_rolls_back_real_batch(request, settings, monkeypatch):
    case, _, coverage, reviewer = prepared_batch(request, settings, monkeypatch, binary=True)
    selection = coverage.selection_review.selection
    before = (
        RightsAction.objects.count(),
        RightsPortabilitySelectionRead.objects.count(),
        RightsPortabilityCoverageRead.objects.count(),
    )
    original = batch.inspect_page
    calls = []

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(True)
        if len(calls) == 2:
            type(selection).objects.filter(pk=selection.pk).update(encrypted_selection="invalid")
        return result

    monkeypatch.setattr(batch, "inspect_page", mutate)
    with pytest.raises(ValidationError):
        batch.inspect_batch(
            reviewer, case.pk, case.version, coverage.pk, uuid4(), REASON, "revisions"
        )
    assert len(calls) == 2
    assert (
        RightsAction.objects.count(),
        RightsPortabilitySelectionRead.objects.count(),
        RightsPortabilityCoverageRead.objects.count(),
    ) == before
    selection.refresh_from_db()
    assert selection.encrypted_selection != "invalid"


def test_single_read_keeps_fresh_default_body_digest(request, settings, monkeypatch):
    case, selection, actor, decisions, first = prepared(request, settings, monkeypatch)
    observed = []
    original = selection_review.fingerprint

    def fingerprint(value):
        if value == selection.encrypted_selection:
            observed.append(value)
        return original(value)

    monkeypatch.setattr(selection_review, "fingerprint", fingerprint)
    with transaction.atomic():
        image_reads.validate_read(first, selection, case, first.proof, decisions[0], actor)
    assert len(observed) == 1


def test_selection_canonical_expected_once_and_domain_output_equal(request, settings, monkeypatch):
    case, selection, _, _, _ = prepared(request, settings, monkeypatch)
    original = selection_store.canonical
    calls = []

    def canonical(value):
        if isinstance(value, dict) and value.get("schema") == "portability-selection-draft-v1":
            calls.append(id(value))
        return original(value)

    monkeypatch.setattr(selection_store, "canonical", canonical)
    with transaction.atomic():
        result = selection_store.validate_selection_evidence(
            selection, selection.assessment_review, case
        )
    assert result == unseal(selection.encrypted_selection)
    assert len(calls) == 2  # One current body and one expected body, each exactly once.
    assert len(set(calls)) == 2


@pytest.mark.parametrize("invalid", [float("nan"), "\ud800", "deep"])
def test_invalid_canonical_values_still_rejected(request, settings, monkeypatch, invalid):
    case, selection, _, _, _ = prepared(request, settings, monkeypatch)
    body = deepcopy(unseal(selection.encrypted_selection))
    value = invalid
    if invalid == "deep":
        value = {}
        for _ in range(201):
            value = {"nested": value}
    body["selection"] = value
    original = selection_store.unseal
    monkeypatch.setattr(
        selection_store,
        "unseal",
        lambda encrypted: (
            deepcopy(body) if encrypted == selection.encrypted_selection else original(encrypted)
        ),
    )
    with (
        transaction.atomic(),
        pytest.raises((ValueError, TypeError, ValidationError, UnicodeError)),
    ):
        selection_store.validate_selection_evidence(selection, selection.assessment_review, case)
