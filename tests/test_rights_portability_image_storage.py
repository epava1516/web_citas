"""Signed binary declarations require exact own inspections before independent review."""

import hashlib
import json
from copy import deepcopy
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsAction,
    RightsPortabilityImageRead,
    RightsPortabilitySelectionReview,
)
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_page_selection import prepare_page, save_page
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_review import record
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("packaged", [False, True])
def test_binary_declarations_require_inspection_approval_and_private_delivery(
    request, settings, monkeypatch, packaged
):
    case, author, baseline, previous_decision, person, _, receipt = prepared_selection(
        request, settings, monkeypatch, False
    )
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    body = unseal(baseline.encrypted_selection)
    selectors, evidence = body["selection"], body["field_evidence"]
    revision_index, revision = next(
        (index, item) for index, item in enumerate(source["revisions"]) if item["images"]
    )
    photo = revision["images"][0]["photo"]
    facts = dict(
        status="eligible",
        basis="contract",
        origin="provided",
        automated=True,
        subject_related=True,
        third_party_reviewed=True,
        reason="Synthetic independent binary image provenance conditions",
        evidence="Synthetic evidence for supplied image and third-party review",
    )
    selected = [
        {
            "row": row_reference("revisions", revision_index, revision),
            "path": "/images/0/photo",
            "photo": photo,
            "content_digest": "a" * 64,
            "conditions": facts,
        }
    ]
    reason = "Prepare explicitly eligible synthetic binary image declaration"
    before = RightsAction.objects.filter(request=case).count()
    with pytest.raises(ValidationError, match="Inspect exact"):
        save_selection(
            author,
            case.pk,
            case.version,
            baseline.assessment_review_id,
            uuid4(),
            baseline.version,
            reason,
            selectors,
            field_evidence=evidence,
            images=selected,
        )
    assert RightsAction.objects.filter(request=case).count() == before
    client = Client()
    client.force_login(author)
    session = client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    response = client.post(
        f"/en/moderation/rights/{case.pk}/image/{photo}/",
        {"purpose": "Inspect synthetic image bytes before portable declaration"},
    )
    assert response.status_code == 200
    selected[0]["content_digest"] = hashlib.sha256(response.content).hexdigest()
    key = uuid4()
    row = save_selection(
        author,
        case.pk,
        case.version,
        baseline.assessment_review_id,
        key,
        baseline.version,
        reason,
        selectors,
        field_evidence=evidence,
        images=selected,
    )
    assert unseal(row.encrypted_selection)["images"] == selected
    assert photo not in row.encrypted_selection
    assert (
        save_selection(
            author,
            case.pk,
            case.version,
            baseline.assessment_review_id,
            key,
            baseline.version,
            reason,
            selectors,
            field_evidence=evidence,
            images=selected,
        ).pk
        == row.pk
    )
    changed = deepcopy(selected)
    changed[0]["conditions"]["evidence"] += " changed"
    with pytest.raises(ValidationError):
        save_selection(
            author,
            case.pk,
            case.version,
            baseline.assessment_review_id,
            key,
            baseline.version,
            reason,
            selectors,
            field_evidence=evidence,
            images=changed,
        )
    reviewer = previous_decision.action.actor
    _, projected = record(reviewer, case.pk, case.version, row.pk, uuid4(), reason)
    assert projected["images"] == selected
    with pytest.raises(ValidationError, match="Independent binary"):
        record(reviewer, case.pk, case.version, row.pk, uuid4(), reason, "review", "approved")
    assert not RightsPortabilitySelectionReview.objects.filter(selection=row).exists()
    field_page = prepare_page(
        author, case.pk, case.version, baseline.assessment_review_id, uuid4(), reason, "profile"
    )
    row = save_page(
        author,
        case.pk,
        field_page["token"],
        uuid4(),
        reason,
        field_page["chosen"],
        field_decisions=field_page["field_decisions"],
    )
    assert unseal(row.encrypted_selection)["images"] == selected
    from apps.safety.rights_portability_export import generate
    from apps.safety.rights_portability_image_read import inspect

    with pytest.raises(PermissionDenied):
        inspect(author, case.pk, case.version, row.pk, photo, uuid4(), reason)
    read_key = uuid4()
    reviewer_client = Client()
    reviewer_client.force_login(reviewer)
    session = reviewer_client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    path = reverse("rights_portability_image_inspect", args=[case.pk, row.pk, photo])
    denied = reviewer_client.get(path)
    assert denied.status_code == 405 and denied["Cache-Control"] == "private, no-store"
    assert reviewer_client.post(path, {}).status_code == 400
    values = {"key": read_key, "version": case.version, "reason": reason}
    protected = Client(enforce_csrf_checks=True)
    protected.cookies = reviewer_client.cookies.copy()
    assert protected.post(path, values).status_code == 403
    result = reviewer_client.post(path, values)
    assert result.status_code == 200 and result["Cache-Control"] == "private, no-store"
    binary_read = RightsPortabilityImageRead.objects.get(action__key=read_key)
    content = result.content
    assert content == response.content
    assert (
        inspect(reviewer, case.pk, case.version, row.pk, photo, read_key, reason)[0].pk
        == binary_read.pk
    )
    decision_key = uuid4()
    approved, _ = record(
        reviewer, case.pk, case.version, row.pk, decision_key, reason, "review", "approved"
    )
    assert approved.image_reads == [binary_read.pk]
    newer, _ = inspect(reviewer, case.pk, case.version, row.pk, photo, uuid4(), reason)
    assert newer.pk != binary_read.pk
    replayed, _ = record(
        reviewer, case.pk, case.version, row.pk, decision_key, reason, "review", "approved"
    )
    assert replayed.pk == approved.pk and replayed.image_reads == [binary_read.pk]
    import io
    import zipfile

    from test_rights_exports import url

    from apps.safety.crypto import seal
    from apps.safety.models import RightsExportDownload, RightsExportImage

    version, export_key = case.version, uuid4()
    if packaged:
        from apps.safety import rights_data_parts

        monkeypatch.setattr(rights_data_parts, "DATA_PART_LIMIT", 256)
    export = generate(author, case.pk, version, row.pk, approved.pk, export_key, reason)
    assert (
        generate(author, case.pk, version, row.pk, approved.pk, export_key, reason).pk == export.pk
    )
    snapshot = RightsExportImage.objects.get(export=export)
    assert not snapshot.encrypted_content.startswith("RIFF")
    public = Client()
    payload = public.post(url(receipt, export), {"key": uuid4()}).json()
    if packaged:
        assert payload["schema"] == "rights-data-manifest-v1"
        fragments = []
        for item in payload["data_parts"]:
            delivered_part = public.post(
                url(receipt, export) + f"part/{item['id']}/", {"key": uuid4()}
            )
            assert delivered_part.status_code == 200
            with zipfile.ZipFile(io.BytesIO(delivered_part.content)) as archive:
                fragments.append(archive.read(item["filename"]))
        payload = json.loads(b"".join(fragments))
    assert payload["images"][0]["attachment"] == str(snapshot.pk)
    assert payload["images"][0]["sha256"] == hashlib.sha256(content).hexdigest()
    assert "conditions" not in str(payload) and "field_evidence" not in payload
    image_path = url(receipt, export) + f"image/{snapshot.pk}/"
    download_key = uuid4()
    assert public.get(image_path).status_code == 405
    downloaded = public.post(image_path, {"key": download_key})
    assert downloaded.status_code == 200 and downloaded.content == content
    assert downloaded["Cache-Control"] == "private, no-store"
    assert public.post(image_path, {"key": download_key}).content == content
    assert RightsExportDownload.objects.filter(image=snapshot).count() == 1
    part = export.parts.exclude(attachments=[]).get()
    part_path = url(receipt, export) + f"part/{part.pk}/"
    packaged = public.post(part_path, {"key": uuid4()})
    assert packaged.status_code == 200
    with zipfile.ZipFile(io.BytesIO(packaged.content)) as archive:
        assert archive.namelist() == [str(snapshot.pk) + ".webp"]
        assert archive.read(archive.namelist()[0]) == content
    before_downloads = RightsExportDownload.objects.filter(export=export).count()
    before_actions = RightsAction.objects.filter(request=case).count()
    # Storage bytes can change without any database field or source digest changing.
    from apps.mediafiles.models import Photo

    derivative = Photo.objects.get(pk=photo).blob.derivative
    altered = bytearray(content)
    altered[-1] ^= 1
    try:
        with derivative.open("wb") as stream:
            stream.write(altered)
        assert public.post(image_path, {"key": uuid4()}).status_code == 404
        assert public.post(part_path, {"key": uuid4()}).status_code == 404
        with pytest.raises(ValidationError):
            generate(author, case.pk, version, row.pk, approved.pk, export_key, reason)
        assert RightsExportDownload.objects.filter(export=export).count() == before_downloads
        assert RightsAction.objects.filter(request=case).count() == before_actions
    finally:
        with derivative.open("wb") as stream:
            stream.write(content)
    assert public.post(image_path, {"key": download_key}).content == content
    assert (
        generate(author, case.pk, version, row.pk, approved.pk, export_key, reason).pk == export.pk
    )
    original = snapshot.encrypted_content
    snapshot.encrypted_content = seal({"synthetic_corruption": True})
    snapshot.save(update_fields=["encrypted_content"])
    assert public.post(image_path, {"key": uuid4()}).status_code == 404
    assert RightsExportDownload.objects.filter(export=export).count() == before_downloads
    snapshot.encrypted_content = original
    snapshot.save(update_fields=["encrypted_content"])
    part.encrypted_content = seal({"synthetic_corruption": True})
    part.save(update_fields=["encrypted_content"])
    assert public.post(part_path, {"key": uuid4()}).status_code == 404
    assert RightsExportDownload.objects.filter(export=export).count() == before_downloads
    case.refresh_from_db()
    assert case.version == version + 1 and case.status == "reviewing"

    # Nonempty binary-read census must detect signed metadata changes without content.
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsRequest
    from apps.safety.tasks import purge_expired_exports

    with transaction.atomic():
        inventory_case = RightsRequest.objects.create(
            submission_key=uuid4(),
            kind="erase",
            person=person,
            received_at=case.received_at,
            initial_due_at=case.initial_due_at,
            receipt_expires_at=case.receipt_expires_at,
        )
        manifest = source_manifest(person, inventory_case)
        entries = {item["model"]: item for item in manifest["entries"]}
        binary_entry = entries["safety.RightsPortabilityImageRead"]
        assert binary_entry["count"] == 2
        assert snapshot.encrypted_content not in str(manifest)
        assert row.encrypted_selection not in str(manifest)
        assert person.subject_id is not None
        account_inventory_case = RightsRequest.objects.create(
            submission_key=uuid4(),
            kind="erase",
            account_subject_id=person.subject_id,
            received_at=case.received_at,
            initial_due_at=case.initial_due_at,
            receipt_expires_at=case.receipt_expires_at,
        )
        account_manifest = source_manifest(None, account_inventory_case)
        account_entries = {item["model"]: item for item in account_manifest["entries"]}
        account_binary_entry = account_entries["safety.RightsPortabilityImageRead"]
        assert account_binary_entry["count"] == 2
        assert snapshot.encrypted_content not in str(account_manifest)
        assert row.encrypted_selection not in str(account_manifest)
        assert author.pk != person.subject_id
        foreign_inventory_case = RightsRequest.objects.create(
            submission_key=uuid4(),
            kind="erase",
            account_subject=author,
            received_at=case.received_at,
            initial_due_at=case.initial_due_at,
            receipt_expires_at=case.receipt_expires_at,
        )
        foreign_manifest = source_manifest(None, foreign_inventory_case)
        foreign_entries = {item["model"]: item for item in foreign_manifest["entries"]}
        assert foreign_entries["safety.RightsPortabilityImageRead"]["count"] == 0
        original_digest = binary_read.content_digest
        RightsPortabilityImageRead.objects.filter(pk=binary_read.pk).update(content_digest="0" * 64)
        changed = source_manifest(person, inventory_case)
        changed_entries = {item["model"]: item for item in changed["entries"]}
        assert (
            changed_entries["safety.RightsPortabilityImageRead"]["state_digest"]
            != binary_entry["state_digest"]
        )
        changed_account = source_manifest(None, account_inventory_case)
        changed_account_entries = {item["model"]: item for item in changed_account["entries"]}
        assert (
            changed_account_entries["safety.RightsPortabilityImageRead"]["state_digest"]
            != account_binary_entry["state_digest"]
        )
        RightsPortabilityImageRead.objects.filter(pk=binary_read.pk).update(
            content_digest=original_digest
        )

    # Expiry purges every transport while preserving signed evidence and source.
    reads_before = list(RightsPortabilityImageRead.objects.filter(selection=row).values())
    selection_before = row.encrypted_selection
    image_metadata = (snapshot.pk, snapshot.photo_id, snapshot.created_at)
    part_ids = list(export.parts.values_list("pk", flat=True))
    export.expires_at = timezone.now() - timedelta(seconds=1)
    export.save(update_fields=["expires_at"])
    assert purge_expired_exports() == 1
    assert purge_expired_exports() == 0
    export.refresh_from_db()
    snapshot.refresh_from_db()
    row.refresh_from_db()
    assert export.encrypted_payload == "" and export.purged_at is not None
    assert snapshot.encrypted_content == ""
    assert (snapshot.pk, snapshot.photo_id, snapshot.created_at) == image_metadata
    assert list(export.parts.values_list("pk", flat=True)) == part_ids
    assert all(value == "" for value in export.parts.values_list("encrypted_content", flat=True))
    assert row.encrypted_selection == selection_before
    assert list(RightsPortabilityImageRead.objects.filter(selection=row).values()) == reads_before
    assert public.post(image_path, {"key": uuid4()}).status_code == 404
    assert public.post(part_path, {"key": uuid4()}).status_code == 404
    assert RightsExportDownload.objects.filter(export=export).count() == before_downloads
