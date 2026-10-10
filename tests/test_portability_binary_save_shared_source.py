"""Native scoped binary save keeps fresh source checks without repeated snapshots."""

from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.listings.models import Revision
from apps.mediafiles.models import Photo
from apps.safety import rights_inspection_source as shared
from apps.safety import rights_portability_image_selection as image_selection
from apps.safety import rights_portability_selection_store as store
from apps.safety import rights_portability_use as use
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsAction,
    RightsImageAccess,
    RightsPortabilitySelection,
    RightsProof,
)

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Validate complete scoped binary page with fresh source and preserved fields"
FACTS = {"status": "eligible", "basis": "contract", "origin": "provided",
         "automated": True, "subject_related": True, "third_party_reviewed": True,
         "reason": REASON, "evidence": "Synthetic reviewed image; no production legal claim"}


def test_binary_page_save_keeps_one_copy_and_fresh_versions_preserving_native_choices(
    request, settings, monkeypatch, record_property
):
    case, author, baseline, _, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    original = unseal(baseline.encrypted_selection)
    page = image_selection.prepare(author, case.pk, case.version, baseline.assessment_review_id,
                                   uuid4(), REASON, 0, 0)
    calls, version_checks = [], []
    native_versions = shared.source_fingerprint

    def checked_versions(*args, **kwargs):
        version_checks.append(True)
        return native_versions(*args, **kwargs)

    monkeypatch.setattr(shared, "source_fingerprint", checked_versions)
    for module in [shared, image_selection, store, use]:
        native = module.source_copy

        def counted(*args, _native=native, **kwargs):
            calls.append(True)
            return _native(*args, **kwargs)

        monkeypatch.setattr(module, "source_copy", counted)
    key = uuid4()
    row = image_selection.save(author, key, page["token"], REASON, True, FACTS)
    body = unseal(row.encrypted_selection)
    assert body["selection"] == original["selection"]
    assert body["field_evidence"] == original["field_evidence"]
    assert body["images"] == [{**page["declaration"], "conditions": FACTS}]
    record_property("full_source_reads_per_save", len(calls))
    assert len(calls) == 1
    assert len(version_checks) == 2
    calls.clear()
    version_checks.clear()
    assert image_selection.save(author, key, page["token"], REASON, True, FACTS).pk == row.pk
    assert len(calls) == 1
    # Drop only private source-sharing arguments to exercise the native fallback.
    for name in ["catalog", "save_selection"]:
        native = getattr(image_selection, name)

        def unshared(*args, _native=native, **kwargs):
            kwargs.pop("_inspection_source", None)
            return _native(*args, **kwargs)

        monkeypatch.setattr(image_selection, name, unshared)
    calls.clear()
    version_checks.clear()
    replay = image_selection.save(author, key, page["token"], REASON, True, FACTS)
    assert replay.pk == row.pk and unseal(replay.encrypted_selection) == body
    assert len(calls) == 8  # Seven native reads plus the enclosing initial copy.


@pytest.mark.parametrize("change", ["source", "permission", "session", "mfa", "proof"])
def test_binary_save_rechecks_late_changes_after_final_snapshot_and_rolls_back(
    request, settings, monkeypatch, change
):
    case, author, baseline, _, person, _, _ = prepared_selection(request, settings, monkeypatch, False)
    page = image_selection.prepare(author, case.pk, case.version, baseline.assessment_review_id,
                                   uuid4(), REASON, 0, 0)
    key = uuid4()
    before = RightsPortabilitySelection.objects.filter(request=case).count()
    native = shared.source_fingerprint
    calls = []

    def changed(*args, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            if change == "source":
                Revision.objects.filter(listing=person.listing).update(description="Synthetic late source drift")
            elif change == "permission":
                author.user_permissions.clear()
            elif change == "session":
                User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
            elif change == "mfa":
                User.objects.filter(pk=author.pk).update(mfa_version=author.mfa_version + 1)
            else:
                RightsProof.objects.filter(pk=baseline.proof_id).update(status="failed")
        return native(*args, **kwargs)

    monkeypatch.setattr(shared, "source_fingerprint", changed)
    with pytest.raises((PermissionDenied, ValidationError)):
        image_selection.save(author, key, page["token"], REASON, True, FACTS)
    assert len(calls) == 2
    assert RightsPortabilitySelection.objects.filter(request=case).count() == before
    assert not RightsAction.objects.filter(key=key).exists()


def test_private_source_context_cannot_be_forged_or_reused_after_exit(request, settings, monkeypatch):
    case, author, baseline, _, person, _, _ = prepared_selection(request, settings, monkeypatch, False)
    key = uuid4()
    with pytest.raises(ValidationError, match="Invalid inspection source"):
        use.consume_approved(author, case.pk, case.version, baseline.assessment_review_id,
                             key, REASON, _inspection_source=object())
    assert not RightsAction.objects.filter(key=key).exists()
    with transaction.atomic(), shared.inspection_source(person, person.listing, case) as context:
        context.get(person, person.listing, case)
    with pytest.raises(ValidationError, match="unavailable or outside"):
        use.consume_approved(author, case.pk, case.version, baseline.assessment_review_id,
                             key, REASON, _inspection_source=context)
    assert not RightsAction.objects.filter(key=key).exists()


@pytest.mark.parametrize("change", ["valid", "missing", "actor", "version", "digest"])
def test_grouped_binary_audit_preserves_two_real_reads_and_exact_scope(
    request, settings, monkeypatch, change, record_property
):
    import test_rights_portability_export_races as fixtures

    from apps.safety import rights_portability_images as images
    from apps.safety.rights_exports import reviewer_case

    original_ready = fixtures.ready

    def two_photos(*args, **kwargs):
        result = original_ready(*args, **kwargs)
        first = result[-1].listing.revisions.first().photos.first()
        Photo.objects.create(revision=first.revision, blob=first.blob, position=1,
                             removed_at=timezone.now())
        return result

    monkeypatch.setattr(fixtures, "ready", two_photos)
    case, author, baseline, decision, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    for number in range(2):
        page = image_selection.prepare(author, case.pk, case.version, baseline.assessment_review_id,
                                       uuid4(), REASON, 0, number)
        row = image_selection.save(author, uuid4(), page["token"], REASON, True, FACTS)
    binding = unseal(row.encrypted_selection)
    assert len(binding["images"]) == 2
    accesses = RightsImageAccess.objects.filter(request=case, actor=author)
    if change == "missing":
        accesses.delete()
    elif change == "actor":
        accesses.update(actor=decision.action.actor)
    elif change == "version":
        accesses.update(case_version=case.version + 1)
    elif change == "digest":
        accesses.update(content_digest="0" * 64)
    queries, reads = [], []
    from apps.safety import rights_exports

    original_content = rights_exports._read_image_blob

    def counted_content(*args, **kwargs):
        reads.append(True)
        return original_content(*args, **kwargs)

    def observe(execute, sql, params, many, execution_context):
        if "safety_rightsimageaccess" in sql.lower():
            queries.append(True)
        return execute(sql, params, many, execution_context)

    monkeypatch.setattr(rights_exports, "_read_image_blob", counted_content)
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = rights_exports.source_copy(person, listing, locked)
        assessment = unseal(row.assessment_review.assessment.encrypted_assessment)
        with connection.execute_wrapper(observe):
            if change == "valid":
                assert images.audited_images(author, locked, person, source, assessment,
                                             binding["images"]) == binding["images"]
                assert len(reads) == 2
            else:
                with pytest.raises(ValidationError, match="Inspect exact portable image content first"):
                    images.audited_images(author, locked, person, source, assessment, binding["images"])
                assert len(reads) == 2
    assert len(queries) == 1
    record_property("binary_audit_select_count", len(queries))


def test_binary_save_rejects_audit_removed_during_real_byte_read_and_rolls_back(
    request, settings, monkeypatch
):
    from apps.safety import rights_exports

    case, author, baseline, _, _, _, _ = prepared_selection(request, settings, monkeypatch, False)
    page = image_selection.prepare(author, case.pk, case.version, baseline.assessment_review_id,
                                   uuid4(), REASON, 0, 0)
    key = uuid4()
    previous_rows = RightsPortabilitySelection.objects.filter(request=case).count()
    previous_accesses = RightsImageAccess.objects.filter(request=case).count()
    assert previous_accesses > 0
    native = rights_exports._read_image_blob
    reads = []

    def removed_during_read(*args, **kwargs):
        result = native(*args, **kwargs)
        reads.append(True)
        RightsImageAccess.objects.filter(request=case).delete()
        return result

    monkeypatch.setattr(rights_exports, "_read_image_blob", removed_during_read)
    with pytest.raises(ValidationError, match="Inspect exact portable image content first"):
        image_selection.save(author, key, page["token"], REASON, True, FACTS)
    assert len(reads) == 1
    assert RightsPortabilitySelection.objects.filter(request=case).count() == previous_rows
    assert not RightsAction.objects.filter(key=key).exists()
    assert RightsImageAccess.objects.filter(request=case).count() == previous_accesses
