"""Account projections include prior purpose evidence without decrypting its contents."""

import pytest
from django.db import transaction
from test_purpose_exception_consumption import approved
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.account_erasure_inventory import source
from apps.safety.models import PurposeRestriction
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def snapshot(case_id):
    with transaction.atomic():
        case, _, _ = locked_case(case_id)
        return source(case)


def test_same_procedure_excluded_other_procedure_visible_and_opaque_cipher_changes_detected(
    request, settings, monkeypatch
):
    case, _, _, plan, _, proposal, _, _ = approved(request, settings, monkeypatch)
    current = snapshot(case.pk)
    rows = {item["model"]: item for item in current["entries"]}
    assert len(rows) == 50
    assert rows["safety.PublicationCalendarEvent"]["count"] == 0
    assert rows["safety.PurposeRestriction"]["count"] == 1
    assert rows["safety.ProcessingPurposePlan"]["count"] >= 1
    assert rows["safety.ProcessingPlanReview"]["count"] >= 1
    assert rows["safety.ProcessingExecution"]["count"] == 1
    for name in [
        "PurposeExceptionProposal",
        "PurposeExceptionRead",
        "PurposeExceptionReview",
        "RetentionReview",
    ]:
        assert rows["safety." + name]["count"] == 0
    assert plan.source_digest == plan.inventory.source_digest
    original = (
        PurposeRestriction.objects.select_related("execution__action")
        .get()
        .execution.action.request_id
    )
    previous = snapshot(original)
    previous_rows = {item["model"]: item for item in previous["entries"]}
    for name in ["PurposeExceptionProposal", "PurposeExceptionRead", "PurposeExceptionReview"]:
        assert previous_rows["safety." + name]["count"] == 1
    assert previous_rows["safety.RetentionReview"]["count"] > 0
    assert proposal.encrypted_scope not in str(previous)
    # Deliberately damaged stored ciphertext tests projection integrity, not a review workflow.
    proposal.encrypted_scope = "Opaque damaged ciphertext must never be decrypted by inventory"
    proposal.save(update_fields=["encrypted_scope"])
    changed = snapshot(original)
    changed_rows = {item["model"]: item for item in changed["entries"]}
    assert (
        changed_rows["safety.PurposeExceptionProposal"]["state_digest"]
        != previous_rows["safety.PurposeExceptionProposal"]["state_digest"]
    )
    assert proposal.encrypted_scope not in str(changed)
    assert snapshot(case.pk) == current
