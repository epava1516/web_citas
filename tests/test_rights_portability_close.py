from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_response_draft import REASON, TEXT
from test_rights_portability_response_races import ready_final_draft

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsNotice, RightsPortabilityClosure, RightsResponse
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_final_response_closes_only_exact_approval_and_replays_without_effects(
    request, settings, monkeypatch, outcome, account_only
):
    case, author, reviewer, subject, _, draft, read_action, receipt = ready_final_draft(
        request, settings, monkeypatch, with_receipt=True, account_only=account_only
    )
    decision = record(
        reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, outcome
    )
    original = case.version, case.response_version, case.initial_due_at
    key = uuid4()
    if outcome == "rejected":
        with pytest.raises(ValidationError, match="approved final draft"):
            close(author, case.pk, case.version, case.response_version, decision.pk, key, REASON)
        assert (
            RightsResponse.objects.count()
            == RightsNotice.objects.count()
            == RightsPortabilityClosure.objects.count()
            == 0
        )
        case.refresh_from_db()
        assert (
            case.status == "reviewing"
            and (case.version, case.response_version, case.initial_due_at) == original
        )
        return
    from django.test import Client
    from django.urls import reverse
    from test_rights_portability_response_draft import operator

    from apps.safety.models import RightsAction

    staff = operator(author)
    path = reverse("rights_portability_response_close", args=[case.pk, decision.pk])
    before = RightsAction.objects.count()
    assert staff.get(path).status_code == 200 and TEXT not in staff.get(path).content.decode()
    assert RightsAction.objects.count() == before
    assert (
        path
        in staff.get(
            reverse("rights_portability_response_prepare", args=[case.pk])
        ).content.decode()
    )
    data = {
        "key": str(key),
        "version": case.version,
        "response_version": case.response_version,
        "reason": REASON,
    }
    result = staff.post(path, data)
    assert result.status_code == 200 and "no-store" in result["Cache-Control"]
    assert TEXT not in result.content.decode()
    assert staff.post(path, data).status_code == 200
    assert Client().get(path).status_code == 302
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(author)
    assert csrf.post(path, data).status_code == 403
    response = RightsResponse.objects.get(key=key)
    assert unseal(response.encrypted_response) == {"text": TEXT, "simulation": True}
    assert (
        close(author, case.pk, original[0], original[1], decision.pk, key, REASON).pk == response.pk
    )
    assert (
        RightsResponse.objects.count()
        == RightsNotice.objects.count()
        == RightsPortabilityClosure.objects.count()
        == 1
    )
    case.refresh_from_db()
    assert case.status == "resolved" and case.scope_status == "unverified"
    assert (case.version, case.response_version, case.initial_due_at) == (
        original[0] + 1,
        original[1] + 1,
        original[2],
    )
    from django.test import Client
    from test_rights_exports import url

    from apps.safety.models import RightsExportDownload
    from apps.safety.rights import case_export_forms

    export = draft.export
    client = Client()
    payload = unseal(export.encrypted_payload)
    assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 200
    assert client.post(url(receipt, export), {"key": uuid4()}).json() == payload
    assert [item["id"] for item in case_export_forms(case)] == [export.pk]
    assert TEXT in client.get(receipt).content.decode()
    binding = RightsPortabilityClosure.objects.get()
    from django.db import transaction

    from apps.safety.erasure_inventory import source_manifest
    from apps.safety.models import RightsRequest

    inventory_case = RightsRequest.objects.create(
        submission_key=uuid4(),
        kind="erase",
        person=case.person,
        account_subject=subject if account_only else None,
        received_at=case.received_at,
        initial_due_at=case.initial_due_at,
        receipt_expires_at=case.receipt_expires_at,
    )

    def closure_inventory():
        with transaction.atomic():
            manifest = source_manifest(case.person, inventory_case)
            assert TEXT not in str(manifest)
            assert draft.encrypted_response not in str(manifest)
            return next(
                row
                for row in manifest["entries"]
                if row["model"] == "safety.RightsPortabilityClosure"
            )

    inventory_before = closure_inventory()
    assert inventory_before["count"] == 1
    original_channel = binding.channel_digest
    binding.channel_digest = "0" * 64
    binding.save(update_fields=["channel_digest"])
    assert closure_inventory()["state_digest"] != inventory_before["state_digest"]
    downloads = RightsExportDownload.objects.count()
    assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 404
    assert RightsExportDownload.objects.count() == downloads
    binding.channel_digest = original_channel
    binding.save(update_fields=["channel_digest"])
    assert closure_inventory() == inventory_before
    assert client.post(url(receipt, export), {"key": uuid4()}).status_code == 200
    with pytest.raises(ValidationError, match="Conflicting"):
        close(author, case.pk, original[0], original[1], decision.pk, key, REASON + " changed")
    User.objects.filter(pk=author.pk).update(session_version=author.session_version + 1)
    with pytest.raises(PermissionDenied):
        close(author, case.pk, original[0], original[1], decision.pk, key, REASON)


def test_final_response_does_not_change_historical_fifty_response_read_boundary(
    request, settings, monkeypatch
):
    from test_rights_portability_response_draft import operator
    from test_rights_verification import read

    from apps.safety.crypto import seal
    from apps.safety.models import RightsAction
    from apps.safety.rights_portability_response_draft import prepare
    from apps.safety.rights_portability_response_review import inspect

    case, author, reviewer, _, _, previous, _ = ready_final_draft(request, settings, monkeypatch)
    RightsResponse.objects.bulk_create(
        [
            RightsResponse(
                key=uuid4(),
                request=case,
                actor=author,
                case_version=case.version,
                response_version=position,
                kind="progress",
                payload_digest="0" * 64,
                encrypted_reason=seal({"reason": REASON}),
                encrypted_response=seal({"text": TEXT, "simulation": True}),
            )
            for position in range(1, 51)
        ]
    )
    case.response_version = 50
    case.save(update_fields=["response_version"])
    read(operator(author), case)
    read(operator(reviewer), case)
    draft = prepare(
        author,
        case.pk,
        case.version,
        case.response_version,
        previous.export_id,
        uuid4(),
        REASON,
        TEXT,
        True,
    )
    read_key = uuid4()
    inspect(reviewer, case.pk, case.version, draft.pk, read_key, REASON)
    decision = record(
        reviewer,
        case.pk,
        case.version,
        draft.pk,
        RightsAction.objects.get(key=read_key).pk,
        uuid4(),
        REASON,
        "approved",
    )
    version, key = case.version, uuid4()
    response = close(author, case.pk, version, 50, decision.pk, key, REASON)
    assert response.response_version == 51
    assert close(author, case.pk, version, 50, decision.pk, key, REASON).pk == response.pk
    case.refresh_from_db()
    assert case.status == "resolved" and case.response_version == 51


def test_closed_portability_delivers_exact_image_and_package_and_rolls_back_tampering(
    request, settings, monkeypatch
):
    import hashlib
    import io
    import zipfile

    from django.test import Client
    from test_rights_exports import url

    from apps.safety.models import RightsExportDownload

    case, author, reviewer, _, _, draft, read_action, receipt = ready_final_draft(
        request, settings, monkeypatch, with_receipt=True, account_only=False, binary=True
    )
    decision = record(
        reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved"
    )
    close(author, case.pk, case.version, case.response_version, decision.pk, uuid4(), REASON)
    export, client = draft.export, Client()
    payload = client.post(url(receipt, export), {"key": uuid4()})
    assert payload.status_code == 200
    image = export.images.get()
    part = export.parts.exclude(attachments=[]).get()
    image_path = url(receipt, export) + f"image/{image.pk}/"
    part_path = url(receipt, export) + f"part/{part.pk}/"
    response = client.post(image_path, {"key": uuid4()})
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert hashlib.sha256(response.content).hexdigest() == payload.json()["images"][0]["sha256"]
    package = client.post(part_path, {"key": uuid4()})
    assert package.status_code == 200
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        assert archive.namelist() == [str(image.pk) + ".webp"]
        assert archive.read(archive.namelist()[0]) == response.content
    for record_to_damage in (image, part):
        original = record_to_damage.encrypted_content
        record_to_damage.encrypted_content = "damaged"
        record_to_damage.save(update_fields=["encrypted_content"])
        before = RightsExportDownload.objects.count()
        for path in (url(receipt, export), image_path, part_path):
            assert client.post(path, {"key": uuid4()}).status_code == 404
        assert RightsExportDownload.objects.count() == before
        record_to_damage.encrypted_content = original
        record_to_damage.save(update_fields=["encrypted_content"])
    assert client.post(image_path, {"key": uuid4()}).content == response.content
    assert client.post(part_path, {"key": uuid4()}).content == package.content
