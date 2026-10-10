"""Real closed-portability grants: operation reuse never crosses token requests."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_object_delivery import staged
from test_rights_portability_response_draft import REASON
from test_rights_portability_response_races import ready_final_draft

from apps.core.models import User
from apps.mediafiles.models import Photo
from apps.safety import rights_exports, rights_portability_export
from apps.safety.models import RightsExportDownload
from apps.safety.rights_object_delivery import authorize_token, stage_delivery
from apps.safety.rights_object_models import RightsObjectDelivery
from apps.safety.rights_portability_close import close
from apps.safety.rights_portability_response_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def closed_grants(request, settings, monkeypatch, tmp_path):
    case, author, reviewer, _, _, draft, read_action, receipt = ready_final_draft(
        request, settings, monkeypatch, with_receipt=True, account_only=False, binary=True
    )
    decision = record(
        reviewer, case.pk, case.version, draft.pk, read_action.pk, uuid4(), REASON, "approved"
    )
    close(author, case.pk, case.version, case.response_version, decision.pk, uuid4(), REASON)
    export, client = draft.export, Client()
    grants = []
    # Each grant has an actual independently recorded recipient download.
    responses = []
    for _ in range(2):
        key = uuid4()
        response = client.post(url(receipt, export), {"key": key})
        assert response.status_code == 200
        responses.append((RightsExportDownload.objects.get(key=key), response))
    settings.RIGHTS_DELIVERY_ROOT = tmp_path
    settings.RIGHTS_PROXY_DELIVERY_ENABLED = True
    settings.RIGHTS_DELIVERY_GENERATION = "synthetic-proxy-scope-v1"
    settings.RIGHTS_DELIVERY_PROXY_SECRET = "synthetic-proxy-secret-" + "x" * 40
    for download, response in responses:
        with transaction.atomic():
            path = stage_delivery(
                export, download, response.content, response["Content-Type"], "rights-profile.json"
            )
        grants.append((path.rsplit("/", 1)[1], RightsObjectDelivery.objects.get(download=download)))
    return case, author, export, grants


def observe(monkeypatch):
    calls, physical = [], []
    validation = rights_portability_export._sealed_or_full
    read = rights_exports._read_image_blob

    def checked(*args, **kwargs):
        calls.append(True)
        return validation(*args, **kwargs)

    def actual_read(*args, **kwargs):
        physical.append(True)
        return read(*args, **kwargs)

    monkeypatch.setattr(rights_portability_export, "_sealed_or_full", checked)
    monkeypatch.setattr(rights_exports, "_read_image_blob", actual_read)
    return calls, physical


def test_closed_tokens_validate_once_per_operation_and_read_physical_bytes_fresh(
    request, settings, monkeypatch, tmp_path
):
    _, _, _, grants = closed_grants(request, settings, monkeypatch, tmp_path)
    calls, physical = observe(monkeypatch)
    for token, grant in grants:
        before = len(physical)
        assert authorize_token(token).pk == grant.pk
        assert len(physical) > before
        assert rights_portability_export._operation.get() is None
    assert len(calls) == 2
    with pytest.raises(Http404):
        authorize_token(grants[0][0])
    assert rights_portability_export._operation.get() is None


@pytest.mark.parametrize(
    "change", ["bytes", "ciphertext", "session", "mfa", "proof", "source", "expired"]
)
def test_second_token_revalidates_original_authority_evidence_and_content(
    request, settings, monkeypatch, tmp_path, change
):
    case, author, export, grants = closed_grants(request, settings, monkeypatch, tmp_path)
    authorize_token(grants[0][0])
    if change == "bytes":
        photo = Photo.objects.get(pk=export.images.get().photo_id)
        with photo.blob.derivative.open("rb") as stream:
            original = stream.read()
        with photo.blob.derivative.open("wb") as stream:
            stream.write(original[:-1] + bytes([original[-1] ^ 1]))
    elif change == "ciphertext":
        image = export.images.get()
        image.encrypted_content = "corrupted"
        image.save(update_fields=["encrypted_content"])
    elif change in {"session", "mfa"}:
        field = change + "_version"
        User.objects.filter(pk=author.pk).update(**{field: getattr(author, field) + 1})
    elif change == "proof":
        export.proof.expires_at = timezone.now() - timedelta(seconds=1)
        export.proof.save(update_fields=["expires_at"])
    elif change == "source":
        person = case.person
        person.rights_version += 1
        person.save(update_fields=["rights_version"])
    else:
        RightsObjectDelivery.objects.filter(pk=grants[1][1].pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
    with pytest.raises(Http404):
        authorize_token(grants[1][0])
    grants[1][1].refresh_from_db()
    assert grants[1][1].consumed_at is None
    assert rights_portability_export._operation.get() is None


def test_failed_physical_validation_resets_scope_before_next_real_token(
    request, settings, monkeypatch, tmp_path
):
    _, _, _, grants = closed_grants(request, settings, monkeypatch, tmp_path)
    native = rights_exports._read_image_blob

    def failed(blob):
        raise ValidationError("Synthetic physical read failure")

    monkeypatch.setattr(rights_exports, "_read_image_blob", failed)
    with pytest.raises(Http404):
        authorize_token(grants[0][0])
    assert rights_portability_export._operation.get() is None
    grants[0][1].refresh_from_db()
    assert grants[0][1].consumed_at is None
    monkeypatch.setattr(rights_exports, "_read_image_blob", native)
    calls, physical = observe(monkeypatch)
    assert authorize_token(grants[1][0]).pk == grants[1][1].pk
    assert len(calls) == 1 and physical
    assert rights_portability_export._operation.get() is None


def test_access_proxy_authorization_and_replay_remain_unchanged(request, settings, tmp_path):
    _, _, _, path, row, _ = staged(request, settings, tmp_path)
    token = path.rsplit("/", 1)[1]
    assert authorize_token(token).pk == row.pk
    with pytest.raises(Http404):
        authorize_token(token)
    assert rights_portability_export._operation.get() is None
