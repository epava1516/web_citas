from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_compilation import review_all
from test_rights_copy_information import draft
from test_rights_exports import prepared, url
from test_rights_verification import read

from apps.core.models import LegalDocument, User
from apps.safety.models import (
    RightsExport,
    RightsExportDownload,
    RightsExportInformationBinding,
    RightsRequest,
)
from apps.safety.rights_copy_information import record as save
from apps.safety.rights_exports import generate, preview
from apps.safety.rights_information_policy import published_policy
from apps.safety.rights_information_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def approved_information(request, settings, monkeypatch, account_only=False):
    person = subject = None
    if account_only:
        case, author, staff, subject, public, receipt = prepared_account(
            request, settings, monkeypatch
        )
    else:
        case, author, staff, public, receipt, person = prepared(request, settings)
    document = LegalDocument.objects.get(slug="privacy", language="es", active=True)
    with transaction.atomic():
        _, digest = published_policy(document.pk, "es")
    value = draft()
    for item in value["access"].values():
        item.update(status="reviewed", source="reviewer", text="Synthetic reviewed information")
    row = save(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        document.version,
        "Prepare synthetic information for independent review",
        value,
        policy_document_id=document.pk,
        expected_policy_digest=digest,
    )

    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_copy_information",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    reason = "Independently review synthetic information for export"
    record(reviewer, case.pk, row.pk, uuid4(), case.version, "inspect", reason)
    decision, _ = record(
        reviewer, case.pk, row.pk, uuid4(), case.version, "review", reason, "approved"
    )
    return case, author, staff, public, receipt, person, subject, row, decision, document, value


@pytest.mark.parametrize("pages_http", [False, True])
@pytest.mark.parametrize("account_only", [False, True])
def test_approved_information_is_exported_and_policy_change_blocks_download(
    request, settings, monkeypatch, pages_http, account_only
):
    case, author, staff, public, receipt, person, subject, row, decision, document, value = (
        approved_information(request, settings, monkeypatch, account_only)
    )
    source = preview(
        author, case.pk, case.version, "Inspect current source before information export"
    )
    export_key = uuid4()
    original_version = case.version
    path_prepare = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    data = {
        "key": str(export_key),
        "version": original_version,
        "reason": "Generate copy including approved information",
        "operation": "generate_pages_with_information",
        "information_review_id": decision.pk,
    }
    if pages_http:
        assert staff.post(path_prepare, data | {"information_review_id": ""}).status_code == 409
        assert not RightsExport.objects.exists()
        review_all(case, author)
        assert staff.post(path_prepare, data).status_code == 302
        assert staff.post(path_prepare, data).status_code == 302
        export = RightsExport.objects.get()
    else:
        export = generate(
            author,
            case.pk,
            export_key,
            case.version,
            "Generate copy including approved information",
            source,
            information_review_id=decision.pk,
        )
    if not pages_http:
        assert (
            generate(
                author,
                case.pk,
                export_key,
                original_version,
                "Generate copy including approved information",
                source,
                information_review_id=decision.pk,
            ).pk
            == export.pk
        )
    binding = RightsExportInformationBinding.objects.get(export=export)
    assert binding.review_id == decision.pk
    with transaction.atomic():
        if account_only:
            from apps.safety.account_erasure_inventory import source as inventory_source

            current = inventory_source(case)
            assert (
                next(
                    item
                    for item in current["entries"]
                    if item["model"] == "safety.RightsExportInformationBinding"
                )["count"]
                == 0
            )
            inventory_case = RightsRequest.objects.create(
                submission_key=uuid4(),
                account_subject=subject,
                kind="erase",
                received_at=case.received_at,
                initial_due_at=case.initial_due_at,
                receipt_expires_at=case.receipt_expires_at,
            )
            manifest = inventory_source(inventory_case)
        else:
            from apps.safety.erasure_inventory import source_manifest

            manifest = source_manifest(person, case)
        entry = next(
            item
            for item in manifest["entries"]
            if item["model"] == "safety.RightsExportInformationBinding"
        )
        assert entry["count"] == 1
        assert row.encrypted_information not in str(manifest)
    path = url(receipt, export)
    response = public.post(
        path, {"key": uuid4(), "purpose": "Download synthetic approved access information"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["additional_information"]["access"] == value["access"]
    assert body["partial"] and body["simulation"]
    assert "additional_rights_information" not in body["pending_review"]
    before = RightsExportDownload.objects.count()
    # Each stored approval component must still validate at delivery time.
    for evidence, field, invalid in [
        (binding, "decision_digest", "0" * 64),
        (binding, "source_digest", "0" * 64),
        (decision, "original_mfa_version", decision.original_mfa_version + 1),
        (decision.read, "original_session_version", decision.read.original_session_version + 1),
        (row, "encrypted_information", "corrupted synthetic ciphertext"),
        (row, "expires_at", timezone.now() - timedelta(seconds=1)),
        (row, "purged_at", timezone.now()),
        (decision, "outcome", "rejected"),
        (decision.action, "payload_digest", "0" * 64),
        (export.proof, "status", "failed"),
    ]:
        original = getattr(evidence, field)
        type(evidence).objects.filter(pk=evidence.pk).update(**{field: invalid})
        assert (
            public.post(
                path, {"key": uuid4(), "purpose": "Reject altered synthetic approval evidence"}
            ).status_code
            == 404
        )
        assert RightsExportDownload.objects.count() == before
        type(evidence).objects.filter(pk=evidence.pk).update(**{field: original})
    assert (
        public.post(
            path, {"key": uuid4(), "purpose": "Download after restoring valid synthetic evidence"}
        ).status_code
        == 200
    )
    before = RightsExportDownload.objects.count()
    LegalDocument.objects.filter(pk=document.pk).update(
        body="Changed synthetic policy after export"
    )
    assert (
        public.post(
            path, {"key": uuid4(), "purpose": "Download after synthetic privacy policy changed"}
        ).status_code
        == 404
    )
    assert RightsExportDownload.objects.count() == before
    if pages_http:
        assert staff.post(path_prepare, data).status_code == 409
    else:
        with pytest.raises(ValidationError):
            generate(
                author,
                case.pk,
                export_key,
                original_version,
                "Generate copy including approved information",
                source,
                information_review_id=decision.pk,
            )


@pytest.mark.parametrize("account_only", [False, True])
def test_new_pending_information_draft_invalidates_previous_approval(
    request, settings, monkeypatch, account_only
):
    case, author, _, _, _, _, _, row, decision, document, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    pending = save(
        author,
        case.pk,
        case.version,
        uuid4(),
        row.version,
        document.version,
        "New synthetic draft requires fresh independent approval",
        draft(),
        policy_document_id=document.pk,
        expected_policy_digest=row.policy_digest,
    )
    assert pending.pk != row.pk
    source = preview(author, case.pk, case.version, "Review source before stale approval rejection")
    before = case.version
    with pytest.raises(ValidationError, match="Current approved access information required"):
        generate(
            author,
            case.pk,
            uuid4(),
            case.version,
            "Reject previous approval after a new pending information draft",
            source,
            information_review_id=decision.pk,
        )
    assert not RightsExport.objects.exists()
    assert not RightsExportInformationBinding.objects.exists()
    case.refresh_from_db()
    assert case.version == before
