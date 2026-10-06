"""Consume an exact coverage approval with current authority and original reads."""

from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsPortabilityCoverageRead
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_evidence import validate_approved_coverage
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_review import record
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_coverage_use import consume_approved_coverage
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


def prepared_covered_selection(request, settings, monkeypatch, account_only, binary=False):
    result = prepared_selection(request, settings, monkeypatch, account_only)
    if not binary:
        return result
    assert not account_only
    case, author, baseline, previous, profile, subject, receipt = result
    from apps.safety.rights_portability_image_read import inspect
    from apps.safety.rights_portability_image_selection import prepare, save
    from apps.safety.rights_portability_selection_review import record as review_selection

    reason = "Inspect synthetic binary before complete covered delivery"
    page = prepare(
        author, case.pk, case.version, baseline.assessment_review_id, uuid4(), reason, 0, 0
    )
    facts = {
        "status": "eligible",
        "basis": "contract",
        "origin": "provided",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": reason,
        "evidence": "Synthetic portable binary provenance and eligibility",
    }
    selected = save(author, uuid4(), page["token"], reason, True, facts)
    reviewer = previous.action.actor
    review_selection(reviewer, case.pk, case.version, selected.pk, uuid4(), reason)
    inspect(
        reviewer, case.pk, case.version, selected.pk, page["declaration"]["photo"], uuid4(), reason
    )
    decision, _ = review_selection(
        reviewer, case.pk, case.version, selected.pk, uuid4(), reason, "review", "approved"
    )
    return case, author, selected, decision, profile, subject, receipt


@pytest.mark.parametrize(
    ("account_only", "binary"),
    [
        pytest.param(False, False, id="profile"),
        pytest.param(True, False, id="account"),
        pytest.param(False, True, id="profile-binary"),
    ],
)
@pytest.mark.parametrize("delivery", ["service", "http"])
def test_use_approved_coverage_revalidates_original_records_and_authority(
    request, settings, monkeypatch, account_only, binary, delivery
):
    case, author, selection, selected_review, profile, subject, receipt = (
        prepared_covered_selection(request, settings, monkeypatch, account_only, binary)
    )
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    original = case.version, case.status, case.initial_due_at
    facts = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic exclusion without production factual claim",
        "evidence": "PRIVATE_COVERAGE_USE_FIXTURE",
    }
    chosen = unseal(selection.encrypted_selection)
    omissions = {name: {} for name in SECTIONS}
    for dataset, reader in SECTIONS.items():
        for index, item in enumerate(reader(source)):
            reference = row_reference(dataset, index, item)
            selected = next(
                (
                    set(row["fields"])
                    for row in chosen["selection"][dataset]
                    if row["row"] == reference
                ),
                set(),
            )
            if any(field["path"] not in selected for field in scalar_fields(item)):
                omissions[dataset][reference] = {"all": facts}
    included = {image["photo"] for image in chosen.get("images", [])}
    images = {
        image["photo"]: facts
        for revision in source["revisions"]
        for image in revision["images"]
        if image["photo"] not in included
    }
    reason = "Consume independently approved synthetic coverage only"
    coverage = save_coverage(
        author, case.pk, case.version, selected_review.pk, uuid4(), 0, reason, omissions, images
    )
    reviewer = User.objects.get(pk=selected_review.action.actor_id)
    for dataset, index, page, binary_page in required_pages(source):
        inspect_page(
            reviewer,
            case.pk,
            case.version,
            coverage.pk,
            uuid4(),
            reason,
            dataset,
            index,
            page,
            binary=binary_page,
        )
    review = record(reviewer, case.pk, case.version, coverage.pk, uuid4(), reason, "approved")
    original_ids = review.read_ids[:]
    import apps.safety.rights_portability_coverage_pages as pages

    real_unseal = pages.unseal
    observed = []
    key = uuid4()

    def audited_unseal(ciphertext):
        if ciphertext == coverage.encrypted_coverage:
            assert transaction.get_connection().in_atomic_block
            assert RightsAction.objects.filter(key=key, operation="coverage_use").exists()
            observed.append(True)
        return real_unseal(ciphertext)

    monkeypatch.setattr(pages, "unseal", audited_unseal)
    used, compiled = consume_approved_coverage(
        author, case.pk, case.version, review.pk, key, reason
    )
    assert used.pk == review.pk and compiled["schema"] == "portability-coverage-v1"
    assert observed
    inspect_page(
        reviewer,
        case.pk,
        case.version,
        coverage.pk,
        uuid4(),
        reason,
        "subject_account" if account_only else "profile",
    )
    assert (
        consume_approved_coverage(author, case.pk, case.version, review.pk, key, reason)[0].pk
        == review.pk
    )
    review.refresh_from_db()
    assert review.read_ids == original_ids
    with transaction.atomic():
        historical = validate_approved_coverage(review, locked, coverage.proof, source)
        assert historical == compiled
        assert RightsAction.objects.filter(key=key, operation="coverage_use").count() == 1
    assert RightsAction.objects.filter(key=key, operation="coverage_use").count() == 1
    with pytest.raises(ValidationError, match="Conflicting"):
        consume_approved_coverage(
            author,
            case.pk,
            case.version,
            review.pk,
            key,
            "Different reason for the same global coverage use key",
        )
    with pytest.raises(PermissionDenied):
        consume_approved_coverage(reviewer, case.pk, case.version, review.pk, uuid4(), reason)
    read = RightsPortabilityCoverageRead.objects.get(pk=original_ids[0])
    digest = read.page_digest
    read.page_digest = "0" * 64
    read.save(update_fields=["page_digest"])
    with transaction.atomic(), pytest.raises(ValidationError, match="page digest changed"):
        validate_approved_coverage(review, locked, coverage.proof, source)
    with pytest.raises(ValidationError):
        consume_approved_coverage(author, case.pk, case.version, review.pk, key, reason)
    read.page_digest = digest
    read.save(update_fields=["page_digest"])
    review.read_ids = original_ids[:-1]
    review.save(update_fields=["read_ids"])
    with pytest.raises(ValidationError):
        consume_approved_coverage(author, case.pk, case.version, review.pk, key, reason)
    review.read_ids = original_ids
    review.outcome = "rejected"
    review.save(update_fields=["read_ids", "outcome"])
    with pytest.raises(ValidationError, match="Approved coverage"):
        consume_approved_coverage(author, case.pk, case.version, review.pk, key, reason)
    review.outcome = "approved"
    review.save(update_fields=["outcome"])
    reviewer.session_version += 1
    reviewer.save(update_fields=["session_version"])
    with pytest.raises(PermissionDenied):
        consume_approved_coverage(author, case.pk, case.version, review.pk, key, reason)
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original

    # Recover the original reviewer epoch after the denial scenario above.
    reviewer.session_version -= 1
    reviewer.save(update_fields=["session_version"])
    from django.test import Client
    from test_rights_exports import url

    from apps.safety.rights_portability_export import generate

    export_key = uuid4()
    if delivery == "service":
        export = generate(
            author,
            case.pk,
            original[0],
            selection.pk,
            selected_review.pk,
            export_key,
            reason,
            coverage_review_id=review.pk,
        )
    else:
        from django.urls import reverse

        from apps.safety.models import RightsExport

        operator = Client()
        operator.force_login(author)
        session = operator.session
        session["mfa_version"] = author.mfa_version
        session.save()
        path = reverse("rights_portability_export", args=[case.pk])
        before = RightsAction.objects.filter(request=case).count()
        response = operator.get(path)
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
        assert facts["evidence"] not in response.content.decode()
        assert RightsAction.objects.filter(request=case).count() == before
        data = {
            "key": str(export_key),
            "version": original[0],
            "review": selected_review.pk,
            "coverage_review": review.pk,
            "reason": reason,
        }
        response = operator.post(path, data)
        assert response.status_code == 200
        export = RightsExport.objects.get(action__key=export_key)
        assert operator.post(path, data).status_code == 200
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(author)
        assert csrf.post(path, data).status_code == 403
        assert Client().get(path).status_code == 302
    payload = unseal(export.encrypted_payload)
    assert payload["export_schema"] == "covered-portability-v1"
    assert payload["partial"] is False and payload["simulation"] is True
    assert payload["pending_review"] == ["final_response"]
    assert facts["evidence"] not in str(payload)
    assert (
        generate(
            author,
            case.pk,
            original[0],
            selection.pk,
            selected_review.pk,
            export_key,
            reason,
            coverage_review_id=review.pk,
        ).pk
        == export.pk
    )
    with pytest.raises(ValidationError, match="Conflicting"):
        generate(author, case.pk, original[0], selection.pk, selected_review.pk, export_key, reason)
    client = Client()
    response = client.post(url(receipt, export), {"key": uuid4()})
    assert response.status_code == 200 and response.json() == payload
    if binary:
        import hashlib

        snapshot = export.images.get()
        image_response = client.post(
            url(receipt, export) + f"image/{snapshot.pk}/", {"key": uuid4()}
        )
        assert image_response.status_code == 200
        assert (
            hashlib.sha256(image_response.content).hexdigest()
            == chosen["images"][0]["content_digest"]
        )
        package = export.parts.exclude(attachments=[]).get()
        assert (
            client.post(url(receipt, export) + f"part/{package.pk}/", {"key": uuid4()}).status_code
            == 200
        )
        assert payload["coverage"]["included_images"] == 1
    binding = export.portability_binding
    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsExportDownload, RightsRequest

    inventory_case = RightsRequest.objects.create(
        submission_key=uuid4(),
        kind="erase",
        person=profile,
        account_subject=subject if account_only else None,
        received_at=case.received_at,
        initial_due_at=case.initial_due_at,
        receipt_expires_at=case.receipt_expires_at,
    )

    def inventory_entry():
        with transaction.atomic():
            manifest = source_manifest(profile, inventory_case)
            assert facts["evidence"] not in str(manifest)
            assert coverage.encrypted_coverage not in str(manifest)
            return next(
                item
                for item in manifest["entries"]
                if item["model"] == "safety.RightsExportPortabilityBinding"
            )

    before = inventory_entry()
    assert before["count"] == 1
    for field in [
        "coverage_review_id",
        "coverage_use_id",
        "coverage_digest",
        "coverage_ciphertext_digest",
        "coverage_decision_digest",
        "coverage_reads_digest",
    ]:
        original_value = getattr(binding, field)
        setattr(binding, field, None if field.endswith("_id") else "0" * 64)
        binding.save(update_fields=[field.removesuffix("_id") if field.endswith("_id") else field])
        assert inventory_entry()["state_digest"] != before["state_digest"]
        downloads = RightsExportDownload.objects.filter(export=export).count()
        assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 404
        assert RightsExportDownload.objects.filter(export=export).count() == downloads
        setattr(binding, field, original_value)
        binding.save(update_fields=[field.removesuffix("_id") if field.endswith("_id") else field])
        assert inventory_entry()["state_digest"] == before["state_digest"]
    assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 200
    case.refresh_from_db()
    assert case.version == original[0] + 1 and case.status == "reviewing"
    assert case.initial_due_at == original[2]
