import hashlib
import io
import json
import zipfile

import pytest
from django.core.exceptions import ValidationError
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.rights_data_parts import data_packages


def test_unicode_json_reconstruction_preserves_all_bytes_and_bounded_zip_sizes():
    original = json.dumps({"rows": ["áé🙂漢字" * 19] * 8}, ensure_ascii=False).encode()
    parts = list(data_packages(original, limit=256))
    assert len(parts) > 1
    restored = bytearray()
    for position, part in enumerate(parts, 1):
        assert part["position"] == position and len(part["content"]) <= 256
        with zipfile.ZipFile(io.BytesIO(part["content"])) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == [part["filename"]]
            fragment = archive.read(part["filename"])
        assert len(fragment) == part["size"]
        assert hashlib.sha256(fragment).hexdigest() == part["sha256"]
        restored.extend(fragment)
    assert bytes(restored) == original
    assert json.loads(restored) == json.loads(original)
    assert list(data_packages(original, limit=256)) == parts


@pytest.mark.parametrize(
    "content,limit", [(b"", 256), ("text", 256), (b"x", 255), (b"x", 67108865)]
)
def test_invalid_data_packages_reject_input(content, limit):
    with pytest.raises(ValidationError):
        list(data_packages(content, limit=limit))


@pytest.mark.django_db(transaction=True)
def test_reviewed_large_copy_manifest_receipt_download_and_purge(request, settings, monkeypatch):
    import uuid
    from datetime import timedelta

    from django.urls import reverse
    from django.utils import timezone
    from test_rights_exports import prepared, url

    from apps.safety import rights_data_parts
    from apps.safety.models import RightsExportDownload
    from apps.safety.rights_exports import generate, preview
    from apps.safety.tasks import purge_expired_exports

    case, actor, _, client, receipt, person = prepared(request, settings)
    revision = person.listing.revisions.first()
    revision.description = "á🙂漢字" * 1000
    revision.save(update_fields=["description"])
    monkeypatch.setattr(rights_data_parts, "DATA_PART_LIMIT", 4096)
    source = preview(
        actor, case.pk, case.version, "Review full source before multipart private delivery"
    )
    export = generate(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Release reviewed multipart private copy",
        source,
    )
    manifest = client.post(url(receipt, export), {"key": uuid.uuid4()}).json()
    assert manifest["schema"] == "rights-data-manifest-v1" and manifest["partial"]
    assert len(manifest["data_parts"]) > 1
    page = client.get(receipt)
    assert page.status_code == 200 and b"Download data package" in page.content
    restored = bytearray()
    secret = receipt.rstrip("/").rsplit("/", 1)[-1]
    for fragment in manifest["data_parts"]:
        path = reverse(
            "rights_part_download",
            kwargs={
                "case_id": case.pk,
                "secret": secret,
                "export_id": export.pk,
                "part_id": fragment["id"],
            },
        )
        key = uuid.uuid4()
        response = client.post(path, {"key": key})
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
        assert len(response.content) <= 4096
        assert f"rights-data-part-{fragment['position']}.zip" in response["Content-Disposition"]
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            content = archive.read(fragment["filename"])
        assert hashlib.sha256(content).hexdigest() == fragment["sha256"]
        assert len(content) == fragment["size"]
        restored.extend(content)
        before = RightsExportDownload.objects.count()
        assert client.post(path, {"key": key}).content == response.content
        assert RightsExportDownload.objects.count() == before
    assert len(restored) == manifest["size"]
    assert hashlib.sha256(restored).hexdigest() == manifest["sha256"]
    delivered = json.loads(restored)
    assert delivered["revisions"] == source["revisions"]
    assert delivered["profile"] == source["profile"]
    export.expires_at = timezone.now() - timedelta(seconds=1)
    export.save(update_fields=["expires_at"])
    assert purge_expired_exports() == 1
    assert not export.parts.exclude(encrypted_content="").exists()
    assert client.post(path, {"key": uuid.uuid4()}).status_code == 404


def test_data_packages_at_real_eight_mib_limit_preserve_large_document():
    from apps.safety.rights_data_parts import DATA_PART_LIMIT

    content = b'{"synthetic":"' + b"x" * (DATA_PART_LIMIT + 1024) + b'"}'
    recovered = bytearray()
    parts = list(data_packages(content))
    assert len(parts) == 2
    for part in parts:
        assert len(part["content"]) <= DATA_PART_LIMIT
        with zipfile.ZipFile(io.BytesIO(part["content"])) as package:
            recovered.extend(package.read(part["filename"]))
    assert bytes(recovered) == content and json.loads(recovered)["synthetic"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("language", ["en", "es"])
def test_mobile_anonymous_data_packages_and_manifest_download(
    live_server, request, settings, monkeypatch, language
):
    import shutil
    import uuid
    from pathlib import Path

    from playwright.sync_api import expect, sync_playwright
    from test_rights_exports import prepared

    from apps.safety import rights_data_parts
    from apps.safety.models import RightsExportDownload
    from apps.safety.rights_exports import generate, preview

    settings.DEBUG = True
    case, actor, _, _, receipt, person = prepared(request, settings)
    revision = person.listing.revisions.first()
    revision.description = "Private synthetic Unicode á🙂漢字" * 150
    revision.save(update_fields=["description"])
    monkeypatch.setattr(rights_data_parts, "DATA_PART_LIMIT", 4096)
    source = preview(
        actor, case.pk, case.version, "Inspect synthetic multipart source for mobile recipient"
    )
    export = generate(
        actor,
        case.pk,
        uuid.uuid4(),
        case.version,
        "Release reviewed multipart source for mobile recipient",
        source,
    )
    receipt = receipt.replace("/en/", f"/{language}/", 1)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + receipt)
            label = "Download private copy" if language == "en" else "Descargar copia privada"
            with page.expect_download() as downloaded:
                page.get_by_role("button", name=label, exact=True).click()
            manifest = json.loads(Path(downloaded.value.path()).read_bytes())
            assert manifest["schema"] == "rights-data-manifest-v1"
            restored = bytearray()
            for fragment in manifest["data_parts"]:
                label = (
                    "Download data package " if language == "en" else "Descargar paquete de datos "
                ) + str(fragment["position"])
                expect(page.get_by_role("button", name=label, exact=True)).to_be_visible()
                with page.expect_download() as downloaded:
                    page.get_by_role("button", name=label, exact=True).click()
                assert (
                    downloaded.value.suggested_filename
                    == f"rights-data-part-{fragment['position']}.zip"
                )
                with zipfile.ZipFile(Path(downloaded.value.path())) as archive:
                    content = archive.read(fragment["filename"])
                assert hashlib.sha256(content).hexdigest() == fragment["sha256"]
                restored.extend(content)
            assert hashlib.sha256(restored).hexdigest() == manifest["sha256"]
            assert json.loads(restored)["revisions"] == source["revisions"]
            page.reload()
            assert "Private synthetic Unicode" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert RightsExportDownload.objects.filter(export=export).count() == 1 + export.parts.count()
