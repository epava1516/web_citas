"""Real PostgreSQL coverage storage, expiry and evidence isolation."""

from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety.crypto import seal, unseal
from apps.safety.models import RightsAction, RightsPortabilityCoverage, RightsRequest
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_selection import row_reference
from apps.safety.tasks import purge_expired_portability_coverage

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_coverage_is_bound_cifred_replayable_and_purged_without_closing(
    request, settings, monkeypatch, account_only
):
    case, author, selection, decision, person, subject, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    body = unseal(selection.encrypted_selection)
    omissions = {name: {} for name in SECTIONS}
    excluded = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic fixture exclusion, not a production factual decision",
        "evidence": "PRIVATE_SYNTHETIC_COVERAGE_EVIDENCE",
    }
    for name, rows in SECTIONS.items():
        selectors = {item["row"]: set(item["fields"]) for item in body["selection"][name]}
        for index, item in enumerate(rows(source)):
            reference = row_reference(name, index, item)
            if {field["path"] for field in scalar_fields(item)} - selectors.get(reference, set()):
                omissions[name][reference] = {"all": excluded}
    images = {
        image["photo"]: excluded for revision in source["revisions"] for image in revision["images"]
    }
    original = case.version, case.status, case.initial_due_at
    reason = "Prepare explicit synthetic omissions for independent coverage review"
    key = uuid4()
    actions_before = RightsAction.objects.filter(request=case).count()
    row = save_coverage(
        author, case.pk, case.version, decision.pk, key, 0, reason, omissions, images
    )
    assert row.version == 1 and row.selection_review_id == decision.pk
    assert row.proof_id == selection.proof_id and row.source_digest == selection.source_digest
    assert row.expires_at <= selection.expires_at
    assert excluded["evidence"] not in row.encrypted_coverage
    assert unseal(row.encrypted_coverage)["omissions"] == omissions
    assert (
        save_coverage(
            author, case.pk, case.version, decision.pk, key, 0, reason, omissions, images
        ).pk
        == row.pk
    )
    assert RightsAction.objects.filter(request=case).count() == actions_before + 2
    assert RightsPortabilityCoverage.objects.filter(request=case).count() == 1
    changed = deepcopy(omissions)
    name = next(name for name in changed if changed[name])
    reference = next(iter(changed[name]))
    changed[name][reference]["all"]["reason"] += " changed"
    with pytest.raises(ValidationError):
        save_coverage(author, case.pk, case.version, decision.pk, key, 0, reason, changed, images)
    missing = deepcopy(omissions)
    missing[name].pop(reference)
    with pytest.raises(ValidationError):
        save_coverage(
            author, case.pk, case.version, decision.pk, uuid4(), 1, reason, missing, images
        )
    original_cipher = row.encrypted_coverage
    action = row.action
    original_reason = action.encrypted_reason
    action.encrypted_reason = seal({})
    action.save(update_fields=["encrypted_reason"])
    with pytest.raises(ValidationError, match="Coverage reason"):
        save_coverage(author, case.pk, case.version, decision.pk, key, 0, reason, omissions, images)
    action.encrypted_reason = original_reason
    action.save(update_fields=["encrypted_reason"])
    original_actor = row.actor_id
    row.actor_id = decision.action.actor_id
    row.save(update_fields=["actor"])
    with pytest.raises(ValidationError, match="Conflicting stored coverage"):
        save_coverage(author, case.pk, case.version, decision.pk, key, 0, reason, omissions, images)
    row.actor_id = original_actor
    row.save(update_fields=["actor"])
    row.encrypted_coverage = seal({"synthetic_corruption": True})
    row.save(update_fields=["encrypted_coverage"])
    with pytest.raises(ValidationError):
        save_coverage(author, case.pk, case.version, decision.pk, key, 0, reason, omissions, images)
    row.encrypted_coverage = original_cipher
    row.save(update_fields=["encrypted_coverage"])
    # Inventory exposes metadata only, preserving the original signed declaration.

    from apps.safety.erasure_inventory import source_manifest

    with transaction.atomic():
        inventory_case = RightsRequest.objects.create(
            submission_key=uuid4(),
            kind="erase",
            person=person,
            account_subject=subject if account_only else None,
            received_at=case.received_at,
            initial_due_at=case.initial_due_at,
            receipt_expires_at=case.receipt_expires_at,
        )
        manifest = source_manifest(person, inventory_case)
        entry = next(
            item
            for item in manifest["entries"]
            if item["model"] == "safety.RightsPortabilityCoverage"
        )
        assert entry["count"] == 1 and row.encrypted_coverage not in str(manifest)
    action_ids = list(RightsAction.objects.filter(request=case).values_list("pk", flat=True))
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save(update_fields=["expires_at"])
    assert purge_expired_portability_coverage() == 1
    assert purge_expired_portability_coverage() == 0
    row.refresh_from_db()
    assert row.encrypted_coverage == "" and row.purged_at is not None
    assert row.selection_review_id == decision.pk and row.coverage_digest
    assert (
        list(RightsAction.objects.filter(request=case).values_list("pk", flat=True)) == action_ids
    )
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
    assert RightsAction.objects.filter(request=case).count() == actions_before + 2


@pytest.mark.parametrize("account_only", [False, True])
def test_pending_coverage_mode_is_signed_and_does_not_close_case(
    request, settings, monkeypatch, account_only
):
    case, author, _, decision, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    original = case.version, case.status, case.initial_due_at
    omissions = {name: {} for name in SECTIONS}
    key = uuid4()
    reason = "Prepare incomplete coverage without inferring any exclusion"
    row = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        key,
        0,
        reason,
        omissions,
        {},
        allow_partial=True,
    )
    assert unseal(row.encrypted_coverage)["allow_partial"] is True
    assert unseal(row.encrypted_coverage)["omissions"] == omissions
    assert (
        save_coverage(
            author,
            case.pk,
            case.version,
            decision.pk,
            key,
            0,
            reason,
            omissions,
            {},
            allow_partial=True,
        ).pk
        == row.pk
    )
    with pytest.raises(ValidationError, match="Conflicting coverage key"):
        save_coverage(author, case.pk, case.version, decision.pk, key, 0, reason, omissions, {})
    with pytest.raises(ValidationError):
        save_coverage(author, case.pk, case.version, decision.pk, uuid4(), 1, reason, omissions, {})
    assert RightsPortabilityCoverage.objects.filter(request=case).count() == 1
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
