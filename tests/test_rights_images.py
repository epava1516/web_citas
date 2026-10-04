import json
import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared, url

from apps.core.models import Person
from apps.safety.models import (
    RightsExport,
    RightsExportDownload,
    RightsExportImage,
    RightsImageAccess,
)
from apps.safety.rights_exports import generate, preview
from apps.safety.tasks import purge_expired_exports

pytestmark = pytest.mark.django_db(transaction=True)


def selection(source, photo):
    image = next(
        image
        for revision in source["revisions"]
        for image in revision["images"]
        if image["photo"] == str(photo.pk)
    )
    image["content_included"] = True
    image["exclusion_code"] = ""


def create_image_copy(request, settings):
    case, user, staff, client, receipt, person = prepared(request, settings)
    source = preview(
        user, case.pk, case.version, "Inspect data and image inventory before private release"
    )
    photo = person.listing.revisions.first().photos.first()
    path = f"/en/moderation/rights/{case.pk}/image/{photo.pk}/"
    denied = staff.get(path)
    assert denied.status_code == 405 and denied["Cache-Control"] == "private, no-store"
    inspected = staff.post(
        path, {"purpose": "Inspect this image for third-party data before release"}
    )
    assert inspected.status_code == 200 and inspected.content.startswith(b"RIFF")
    assert inspected["Cache-Control"] == "private, no-store"
    selection(source, photo)
    export = generate(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Release independently reviewed scoped image copy",
        source,
    )
    image = RightsExportImage.objects.get(export=export)
    return case, staff, client, receipt, export, image, inspected.content


def test_reviewed_image_snapshot_is_encrypted_private_and_download_audited(
    request, settings, caplog
):
    case, staff, client, receipt, export, image, content = create_image_copy(request, settings)
    assert not image.encrypted_content.startswith("RIFF") and "WEBP" not in image.encrypted_content
    copy = client.post(url(receipt, export), {"key": uuid.uuid4()}).json()
    projected = next(
        item
        for revision in copy["revisions"]
        for item in revision["images"]
        if item["content_included"]
    )
    assert projected["attachment"] == str(image.pk)
    path = url(receipt, export) + f"image/{image.pk}/"
    assert client.get(path).status_code == 405
    key = {"key": uuid.uuid4()}
    response = client.post(path, key)
    assert response.status_code == 200 and response.content == content
    assert response["Content-Type"] == "image/webp"
    assert response["Content-Disposition"] == 'attachment; filename="rights-image.webp"'
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert client.post(path, key).content == content
    assert RightsExportDownload.objects.filter(image=image).count() == 1
    # Reusing a JSON download key for a different attachment is not the same operation.
    assert client.post(url(receipt, export), key).status_code == 409
    assert Client(enforce_csrf_checks=True).post(path, key).status_code == 403
    assert receipt.rstrip("/").rsplit("/", 1)[-1] not in caplog.text
    assert b"Download reviewed image" in client.get(receipt).content
    settings.PRODUCTION = True
    assert client.post(path, key).status_code == 404
    settings.PRODUCTION = False
    case.refresh_from_db()
    case.version += 1
    case.save(update_fields=["version"])
    assert client.post(path, key).status_code == 404
    assert (
        staff.post(
            f"/en/moderation/rights/{case.pk}/image/{image.photo_id}/",
            {"purpose": "Old proof cannot inspect image after generation"},
        ).status_code
        == 409
    )


def test_selected_image_needs_current_audited_bytes_and_foreign_photos_are_inaccessible(
    request, settings
):
    case, user, staff, _, _, person = prepared(request, settings)
    source = preview(user, case.pk, case.version, "Inspect own image inventory before disclosure")
    photo = person.listing.revisions.first().photos.first()
    selection(source, photo)
    with pytest.raises(ValidationError):
        generate(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "Attempt release without image inspection",
            source,
        )
    other = (
        Person.objects.get(subject__username="fixture-v1-model-b")
        .listing.revisions.first()
        .photos.first()
    )
    # Model B may have no photograph in the synthetic directory; use the unrelated individual.
    if other is None:
        other = (
            Person.objects.get(individual__username="fixture-v1-individual")
            .listing.revisions.first()
            .photos.first()
        )
    assert other
    path = f"/en/moderation/rights/{case.pk}/image/{other.pk}/"
    assert (
        staff.post(
            path, {"purpose": "Try inspecting an image from a different profile"}
        ).status_code
        == 404
    )
    assert not RightsImageAccess.objects.exists()
    path = f"/en/moderation/rights/{case.pk}/image/{photo.pk}/"
    assert staff.post(path, {"purpose": "bad"}).status_code == 400
    assert (
        staff.post(
            path, {"purpose": "Inspect current image for confidential third-party content"}
        ).status_code
        == 200
    )
    RightsImageAccess.objects.update(content_digest="0" * 64)
    with pytest.raises(ValidationError):
        generate(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "Attempt stale inspected content release",
            source,
        )
    assert not RightsExport.objects.exists()
    assert not RightsExportImage.objects.exists()
    # A physical derivative change also invalidates the inspection, even if inventory fields stay equal.
    assert (
        staff.post(
            path, {"purpose": "Reinspect current bytes before generating the copy"}
        ).status_code
        == 200
    )
    import io

    from django.core.files.base import ContentFile
    from PIL import Image

    changed = io.BytesIO()
    Image.new("RGB", (64, 64), "blue").save(changed, "WEBP")
    photo.blob.derivative.save(
        "rights-synthetic-change.webp", ContentFile(changed.getvalue()), save=True
    )
    with pytest.raises(ValidationError):
        generate(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "Attempt release after derivative bytes changed",
            source,
        )
    assert not RightsExport.objects.exists()
    assert not RightsExportImage.objects.exists()


def test_expired_export_purges_image_snapshots_and_mismatch_attachment_is_rejected(
    request, settings
):
    _, _, client, receipt, export, image, _ = create_image_copy(request, settings)
    assert (
        client.post(
            url(receipt, export) + f"image/{uuid.uuid4()}/", {"key": uuid.uuid4()}
        ).status_code
        == 404
    )
    RightsExport.objects.filter(pk=export.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert purge_expired_exports.run() == 1
    export.refresh_from_db()
    image.refresh_from_db()
    assert export.purged_at and not export.encrypted_payload and not image.encrypted_content
    assert purge_expired_exports.run() == 0
    assert (
        client.post(url(receipt, export) + f"image/{image.pk}/", {"key": uuid.uuid4()}).status_code
        == 404
    )


def test_mobile_review_select_generate_and_private_image_download(
    live_server, request, settings, tmp_path
):
    import shutil
    from pathlib import Path

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, receipt, _ = prepared(request, settings)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/export/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Inspect source and own image inventory before release"
            )
            page.get_by_role("button", name="Record copy action", exact=True).click()
            expect(page.locator("[name=copy]")).not_to_have_value("")
            source = json.loads(page.locator("[name=copy]").input_value())
            image = next(image for revision in source["revisions"] for image in revision["images"])
            purpose = page.locator("form[target=_blank]").first.locator("[name=purpose]")
            purpose.fill("Inspect image for third-party information before release")
            with page.expect_popup() as popup:
                page.get_by_role("button", name="View and audit image", exact=True).first.click()
            reviewed = popup.value
            reviewed.wait_for_load_state()
            assert "/image/" in reviewed.url
            reviewed.close()
            image["content_included"], image["exclusion_code"] = True, ""
            page.locator("[name=copy]").fill(json.dumps(source))
            page.locator("[name=reason]").fill(
                "Release independently reviewed account and image copy"
            )
            page.get_by_role("button", name="Record copy action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt)
            with anonymous.expect_download() as download:
                anonymous.get_by_role("button", name="Download reviewed image", exact=True).click()
            content = Path(download.value.path()).read_bytes()
            assert content.startswith(b"RIFF") and content[8:12] == b"WEBP"
            assert "fixture-model-a@example.invalid" not in anonymous.content()
        finally:
            browser.close()
