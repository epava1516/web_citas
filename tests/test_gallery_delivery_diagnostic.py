"""Real browser image scheduling with owned synthetic files and native photo access."""

import hashlib
import io
import os
import shutil
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from urllib.parse import urlsplit

import imagehash
import pytest
from django.core.files.base import ContentFile
from django.db import connection, connections
from django.test import Client
from django.urls import reverse
from django.utils import translation
from PIL import Image
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, synthetic_image  # noqa: F401

from apps.core.models import Person
from apps.listings import publication_state
from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Blob, Photo
from apps.mediafiles.similarity import compute_signature

pytestmark = pytest.mark.django_db(transaction=True)


def gallery_fixture(request):
    request.getfixturevalue("directory")
    listing = Person.objects.get(individual__username="fixture-v1-individual").listing
    revision = listing.approved_revision
    assert revision.photos.filter(removed_at__isnull=True).count() == 1
    for position in range(1, 8):
        image = synthetic_image(810000 + position).resize((1600, 1200), Image.Resampling.LANCZOS)
        original, derivative = io.BytesIO(), io.BytesIO()
        image.save(original, format="PNG")
        image.save(derivative, format="WEBP", quality=85, method=4)
        signature = compute_signature(image)
        blob = Blob.objects.create(
            sha256=hashlib.sha256(original.getvalue()).hexdigest(), width=image.width,
            height=image.height, status="ready", signature=asdict(signature),
            phash=str(imagehash.phash(image)),
            regional_hashes=[f"{value:016x}" for _, value in signature.window_hashes],
        )
        blob.original.save(f"gallery-{position}.png", ContentFile(original.getvalue()))
        blob.derivative.save(f"gallery-{position}.webp", ContentFile(derivative.getvalue()))
        # These are explicit approved display fixtures, not a verification of
        # uploading, similarity review or approval workflows.
        Photo.objects.create(revision=revision, blob=blob, position=position,
                             approved=True, comparison_complete=True)
    description = "\n".join(
        f"Synthetic biography {i:02d}: music, books and walks." for i in range(80)
    )
    assert len(description) < 6000
    Revision.objects.filter(pk=revision.pk).update(
        description=description, description_alternative=description,
    )
    publication_state.refresh_all()
    photos = list(revision.photos.filter(approved=True, removed_at__isnull=True).select_related("blob"))
    assert len(photos) == 8
    bodies, dimensions = [], []
    for photo in photos:
        with photo.blob.derivative.open("rb") as stream:
            body = stream.read()
        with Image.open(io.BytesIO(body)) as decoded:
            assert decoded.format == "WEBP" and not decoded.getexif()
            dimensions.append(decoded.size)
        bodies.append(body)
    return listing, photos, bodies, dimensions


@pytest.mark.parametrize("viewport", ["mobile", "desktop"])
def test_gallery_delivery_browser_diagnostic(live_server, request, settings, record_property, viewport):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    listing, photos, bodies, dimensions = gallery_fixture(request)
    size = {"width": 390, "height": 844} if viewport == "mobile" else {"width": 1280, "height": 800}
    locations = {}
    for language in ["es", "en"]:
        with translation.override(language):
            detail = reverse("listing_detail", args=[listing.pk])
            paths = [reverse("public_photo", args=[listing.pk, photo.pk]) for photo in photos]
        assert Client().get(detail).status_code == 200
        locations[language] = detail, paths

    def set_status(status):
        try:
            return Listing.objects.filter(pk=listing.pk).update(status=status)
        finally:
            connections.close_all()

    reports = []
    with ThreadPoolExecutor(max_workers=1) as writer, sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            for language in ["es", "en"]:
                assert writer.submit(set_status, "published").result(timeout=15) == 1
                detail, paths = locations[language]
                context = browser.new_context(viewport=size, device_scale_factor=1)
                try:
                    page = context.new_page()
                    image_responses, asset_responses = [], []

                    def response_received(response):
                        path = urlsplit(response.url).path
                        if path in paths:
                            image_responses.append(response)
                        elif path.startswith(settings.STATIC_URL):
                            asset_responses.append(response)

                    page.on("response", response_received)
                    page.goto(live_server.url + detail, wait_until="networkidle")
                    images = page.locator(".gallery img")
                    expect(images).to_have_count(8)
                    assert images.evaluate_all("imgs => imgs.map(img => new URL(img.src).pathname)") == paths
                    # Preserve the first photo's ordinary immediate loading.
                    expect(images.first).to_have_js_property("naturalWidth", dimensions[0][0])
                    assert page.evaluate("window.scrollY") == 0
                    gallery = page.locator(".gallery").bounding_box()
                    assert gallery and gallery["y"] > size["height"]
                    initial = list(image_responses)
                    initial_bytes = sum(len(response.body()) for response in initial)
                    loading = images.evaluate_all("imgs => imgs.map(img => img.loading || 'eager')")
                    for index in range(8):
                        image = images.nth(index)
                        image.scroll_into_view_if_needed()
                        expect(image).to_have_js_property("naturalWidth", dimensions[index][0])
                        expect(image).to_have_js_property("naturalHeight", dimensions[index][1])
                    page.wait_for_load_state("networkidle")
                    assert Counter(urlsplit(r.url).path for r in image_responses) == Counter(paths)
                    for response in image_responses:
                        index = paths.index(urlsplit(response.url).path)
                        assert response.status == 200
                        assert response.headers["content-type"] == "image/webp"
                        assert response.headers["cache-control"] == "no-store"
                        assert response.body() == bodies[index]
                    assets = []
                    for response in asset_responses:
                        assert response.status == 200
                        body = response.body()
                        assets.append(dict(path=urlsplit(response.url).path, bytes=len(body),
                                           sha256=hashlib.sha256(body).hexdigest(),
                                           encoding=response.headers.get("content-encoding", "identity")))
                    assert {a["path"].rsplit("/", 1)[-1] for a in assets} >= {"app.css", "form-errors.js"}
                    assert writer.submit(set_status, "paused").result(timeout=15) == 1
                    denied = page.request.get(live_server.url + paths[0], headers={
                        "If-None-Match": '"stale-gallery"',
                        "If-Modified-Since": "Wed, 01 Jan 2031 00:00:00 GMT",
                    })
                    assert denied.status == 404
                    reports.append(dict(
                        language=language, viewport=viewport, viewport_size=size,
                        initial_photo_requests=len(initial), initial_photo_body_bytes=initial_bytes,
                        complete_photo_requests=len(image_responses),
                        complete_photo_body_bytes=sum(map(len, bodies)),
                        photo_sha256=[hashlib.sha256(body).hexdigest() for body in bodies],
                        dimensions=dimensions, loading=loading, gallery_top=gallery["y"],
                        assets=assets, paused_photo_status=denied.status,
                    ))
                finally:
                    context.close()
            record_property("gallery_delivery_diagnostic", dict(
                browser_version=browser.version, reports=reports,
                scope="Synthetic approved display fixtures; real HTTP/files/browser; not upload/similarity approval, Internet capacity or LCP verification",
            ))
        finally:
            browser.close()
