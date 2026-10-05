"""Every data package retains the same approved-information delivery guard."""

import hashlib
import io
import json
import zipfile
from uuid import uuid4

import pytest
from django.urls import reverse
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import url
from test_rights_information_export import approved_information

from apps.core.models import LegalDocument
from apps.safety import rights_data_parts
from apps.safety.models import RightsExportDownload
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_bound_packages_reconstruct_approved_information_and_reject_policy_change(
    request, settings, monkeypatch, account_only
):
    case, actor, _, public, receipt, _, _, _, decision, document, value = approved_information(
        request, settings, monkeypatch, account_only
    )
    # Small test threshold exercises packaging; it is not an 8MiB load measurement.
    monkeypatch.setattr(rights_data_parts, "DATA_PART_LIMIT", 1024)
    reason = "Release synthetic approved access information through data packages"
    source = preview(actor, case.pk, case.version, reason)
    export = generate(
        actor, case.pk, uuid4(), case.version, reason, source, information_review_id=decision.pk
    )
    response = public.post(url(receipt, export), {"key": uuid4(), "purpose": reason})
    assert response.status_code == 200
    manifest = response.json()
    assert manifest["schema"] == "rights-data-manifest-v1"
    assert len(manifest["data_parts"]) > 1
    secret = receipt.rstrip("/").rsplit("/", 1)[-1]
    reconstructed = bytearray()
    paths = []
    for part in manifest["data_parts"]:
        path = reverse(
            "rights_part_download",
            kwargs={
                "case_id": case.pk,
                "secret": secret,
                "export_id": export.pk,
                "part_id": part["id"],
            },
        )
        paths.append(path)
        response = public.post(path, {"key": uuid4(), "purpose": reason})
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert len(response.content) <= 1024
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            fragment = archive.read(part["filename"])
        assert hashlib.sha256(fragment).hexdigest() == part["sha256"]
        assert len(fragment) == part["size"]
        reconstructed.extend(fragment)
    assert len(reconstructed) == manifest["size"]
    assert hashlib.sha256(reconstructed).hexdigest() == manifest["sha256"]
    copy = json.loads(reconstructed)
    assert copy["additional_information"]["access"] == value["access"]
    assert copy["partial"] and copy["simulation"]
    assert "additional_rights_information" not in copy["pending_review"]
    before = RightsExportDownload.objects.count()
    LegalDocument.objects.filter(pk=document.pk).update(
        body="Policy changed after packaged release"
    )
    for path in paths:
        assert public.post(path, {"key": uuid4(), "purpose": reason}).status_code == 404
    assert RightsExportDownload.objects.count() == before
