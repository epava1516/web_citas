import io
import uuid
import zipfile
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_images import create_image_copy

from apps.safety.models import RightsExportDownload
from apps.safety.tasks import purge_expired_exports

pytestmark = pytest.mark.django_db(transaction=True)


def test_reviewed_part_download_is_scoped_audited_and_purged(request, settings):
    _, _, client, receipt, export, image, content = create_image_copy(request, settings)
    part = export.parts.get()
    assert not part.encrypted_content.startswith("PK")
    path = receipt + f"export/{export.pk}/part/{part.pk}/"
    data = {"key": uuid.uuid4()}
    assert client.get(path).status_code == 405
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    response = client.post(path, data)
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.namelist() == [str(image.pk) + ".webp"]
        assert archive.read(archive.namelist()[0]) == content
    assert client.post(path, data).content == response.content
    assert RightsExportDownload.objects.filter(part=part).count() == 1
    assert client.post(receipt + f"export/{export.pk}/", data).status_code == 409
    assert b"Download reviewed package" in client.get(receipt).content
    export.expires_at = timezone.now() - timedelta(seconds=1)
    export.save(update_fields=["expires_at"])
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404
    assert purge_expired_exports() == 1
    part.refresh_from_db()
    assert part.encrypted_content == "" and purge_expired_exports() == 0


def test_generation_over_64mib_delivers_every_reviewed_image_in_bounded_parts(request, settings):
    import hashlib
    import random

    from django.core.files.base import ContentFile
    from PIL import Image
    from test_rights_exports import prepared
    from test_rights_images import selection

    from apps.mediafiles.models import Blob, Photo
    from apps.safety.rights_exports import generate, preview

    case, reviewer, staff, client, receipt, person = prepared(request, settings)
    revision = person.listing.revisions.first()
    photos = []
    expected = {}
    total = 0
    for index in range(8):
        # Real synthetic WebP files; bypasses ingestion solely to prepare retained large snapshots.
        bitmap = Image.frombytes(
            "RGB", (2048, 1536), random.Random(index).randbytes(2048 * 1536 * 3)
        )
        output = io.BytesIO()
        bitmap.save(output, format="WEBP", lossless=True, method=0)
        content = output.getvalue()
        assert len(content) <= 10 * 1024 * 1024
        total += len(content)
        blob = Blob.objects.create(
            sha256=hashlib.sha256(content).hexdigest(), status="ready", width=2048, height=1536
        )
        blob.derivative.save(f"synthetic-part-{index}.webp", ContentFile(content))
        photo = Photo.objects.create(revision=revision, blob=blob, position=index + 10)
        photos.append(photo)
        expected[str(photo.pk)] = hashlib.sha256(content).hexdigest()
    assert total > 64 * 1024 * 1024
    source = preview(
        reviewer, case.pk, case.version, "Inspect synthetic retained large-image copy source"
    )
    for photo in photos:
        response = staff.post(
            f"/en/moderation/rights/{case.pk}/image/{photo.pk}/",
            {"purpose": "Review synthetic large image before scoped private release"},
        )
        assert response.status_code == 200
        selection(source, photo)
    export = generate(
        reviewer,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Release reviewed synthetic large image copy in parts",
        source,
    )
    assert export.parts.count() >= 2
    mapping = {str(image.pk): str(image.photo_id) for image in export.images.all()}
    recovered = {}
    for part in export.parts.order_by("position"):
        response = client.post(
            receipt + f"export/{export.pk}/part/{part.pk}/", {"key": uuid.uuid4()}
        )
        assert response.status_code == 200 and len(response.content) <= 64 * 1024 * 1024
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for name in archive.namelist():
                photo_id = mapping[name[:-5]]
                assert photo_id not in recovered
                recovered[photo_id] = hashlib.sha256(archive.read(name)).hexdigest()
    assert recovered == expected


@pytest.mark.parametrize("language", ["en", "es"])
def test_mobile_anonymous_reviewed_package_download(live_server, request, settings, language):
    import shutil
    from pathlib import Path

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    _, _, _, receipt, export, image, content = create_image_copy(request, settings)
    part = export.parts.get()
    receipt = receipt.replace("/en/", f"/{language}/", 1)
    label = "Download reviewed package 1" if language == "en" else "Descargar paquete revisado 1"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + receipt)
            expect(page.get_by_role("button", name=label, exact=True)).to_be_visible()
            with page.expect_download() as downloaded:
                page.get_by_role("button", name=label, exact=True).click()
            assert downloaded.value.suggested_filename == "rights-part.zip"
            with zipfile.ZipFile(Path(downloaded.value.path())) as archive:
                assert archive.read(str(image.pk) + ".webp") == content
            page.reload()
            assert "rights-private@example.invalid" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert RightsExportDownload.objects.filter(part=part).count() == 1
