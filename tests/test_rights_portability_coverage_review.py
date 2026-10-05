"""Independent coverage decisions, synthetic facts and PostgreSQL."""

from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsPortabilityCoverageRead,
    RightsPortabilityCoverageReview,
    RightsRequest,
)
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_review import record
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("complete", [False, True])
def test_independent_decision_requires_all_pages_and_full_coverage_for_approval(
    request, settings, monkeypatch, complete, account_only
):
    case, author, selection, decision, profile, subject, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    reason = "Review synthetic coverage without production factual claims"
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    facts = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic fixture exclusion without production factual claim",
        "evidence": "PRIVATE_SYNTHETIC_COVERAGE_REVIEW",
    }
    chosen = unseal(selection.encrypted_selection)["selection"]
    omissions = {name: {} for name in SECTIONS}
    if complete:
        for dataset, reader in SECTIONS.items():
            for index, row in enumerate(reader(source)):
                reference = row_reference(dataset, index, row)
                selected = next(
                    (set(item["fields"]) for item in chosen[dataset] if item["row"] == reference),
                    set(),
                )
                if any(item["path"] not in selected for item in scalar_fields(row)):
                    omissions[dataset][reference] = {"all": facts}
    included_images = {
        item["photo"] for item in unseal(selection.encrypted_selection).get("images", [])
    }
    image_omissions = (
        {
            image["photo"]: facts
            for revision in source["revisions"]
            for image in revision["images"]
            if image["photo"] not in included_images
        }
        if complete
        else {}
    )
    row = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        reason,
        omissions,
        image_omissions,
        allow_partial=True,
    )
    reviewer = User.objects.get(pk=decision.action.actor_id)
    with pytest.raises(ValidationError, match="Inspect every current"):
        record(reviewer, case.pk, case.version, row.pk, uuid4(), reason, "approved")
    for dataset, index, page, binary in required_pages(source):
        inspect_page(
            reviewer,
            case.pk,
            case.version,
            row.pk,
            uuid4(),
            reason,
            dataset,
            index,
            page,
            binary=binary,
        )
    outcome = "approved" if complete else "rejected"
    if not complete:
        with pytest.raises(ValidationError):
            record(reviewer, case.pk, case.version, row.pk, uuid4(), reason, "approved")
    key = uuid4()
    result = record(reviewer, case.pk, case.version, row.pk, key, reason, outcome)
    original_ids = result.read_ids[:]
    inspect_page(
        reviewer,
        case.pk,
        case.version,
        row.pk,
        uuid4(),
        reason,
        "subject_account" if account_only else "profile",
    )
    assert record(reviewer, case.pk, case.version, row.pk, key, reason, outcome).pk == result.pk
    result.refresh_from_db()
    assert result.read_ids == original_ids
    assert RightsPortabilityCoverageReview.objects.filter(coverage=row).count() == 1
    with pytest.raises(PermissionDenied):
        record(author, case.pk, case.version, row.pk, uuid4(), reason, outcome)
    from apps.safety.erasure_inventory import source_manifest

    with transaction.atomic():
        inventory_case = RightsRequest.objects.create(
            submission_key=uuid4(),
            kind="erase",
            person=profile,
            account_subject=subject if account_only else None,
            received_at=case.received_at,
            initial_due_at=case.initial_due_at,
            receipt_expires_at=case.receipt_expires_at,
        )
        before = source_manifest(profile, inventory_case)
        entries = {item["model"]: item for item in before["entries"]}
        read_name = "safety.RightsPortabilityCoverageRead"
        review_name = "safety.RightsPortabilityCoverageReview"
        assert entries[read_name]["count"] == len(original_ids) + 1
        assert entries[review_name]["count"] == 1
        assert row.encrypted_coverage not in str(before)
        assert facts["evidence"] not in str(before)
        read = RightsPortabilityCoverageRead.objects.get(pk=original_ids[0])
        digest = read.page_digest
        read.page_digest = "0" * 64
        read.save(update_fields=["page_digest"])
        altered = {
            item["model"]: item for item in source_manifest(profile, inventory_case)["entries"]
        }
        assert altered[read_name]["state_digest"] != entries[read_name]["state_digest"]
        read.page_digest = digest
        read.save(update_fields=["page_digest"])
        original_digest = result.coverage_digest
        result.coverage_digest = "0" * 64
        result.save(update_fields=["coverage_digest"])
        altered = {
            item["model"]: item for item in source_manifest(profile, inventory_case)["entries"]
        }
        assert altered[review_name]["state_digest"] != entries[review_name]["state_digest"]
        result.coverage_digest = original_digest
        result.save(update_fields=["coverage_digest"])
    result.read_ids = original_ids[:-1]
    result.save(update_fields=["read_ids"])
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, case.version, row.pk, key, reason, outcome)
    case.refresh_from_db()
    assert case.version == locked.version and case.status == locked.status
