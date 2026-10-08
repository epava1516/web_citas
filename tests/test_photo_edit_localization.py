"""Photo handler messages with real locks/HTTP; queued fixture avoids duplicating ingestion."""

import shutil

import pytest
from django.db import connection
from django.test import Client
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import LegalAcceptance, User
from apps.listings.models import Revision
from apps.mediafiles.models import Blob, Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_photo_edit_rejects_localized_and_effects_preserved(
    request, settings, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    _, person, client = request.getfixturevalue("scenario")
    assert client.post(f"/{language}/person/{person.pk}/listing/start/").status_code == 302
    revision = Revision.objects.get()
    photos = [
        Photo.objects.create(
            revision=revision, blob=Blob.objects.create(sha256=str(i) * 64), position=i
        )
        for i in range(2)
    ]
    before = revision.edit_version

    def snapshot():
        return list(
            Photo.objects.order_by("position", "created_at").values_list(
                "pk", "position", "removed_at"
            )
        ), Revision.objects.get(pk=revision.pk).edit_version

    original = snapshot()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            draft = live_server.url + f"/{language}/draft/{revision.pk}/3/"
            page.goto(draft)
            button = page.locator("form[action$='/reorder/']").first.locator("button").first
            button.evaluate("e=>e.value='unknown'")
            with page.expect_response(lambda r: r.request.method == "POST") as r:
                button.click()
            assert r.value.status == 400
            expect(page.locator("body")).to_have_text(
                "Invalid direction" if language == "en" else "Dirección inválida"
            )
            assert db_sync(snapshot) == original
            for action in ["reorder", "remove"]:
                page.goto(draft)
                db_sync(lambda: Revision.objects.filter(pk=revision.pk).update(status="pending"))
                button = page.locator(f"form[action$='/{action}/']").first.locator("button").first
                with page.expect_response(lambda r: r.request.method == "POST") as r:
                    button.click()
                assert r.value.status == 409
                expect(page.locator("body")).to_have_text(
                    "Revision not editable" if language == "en" else "Revisión no editable"
                )
                assert db_sync(snapshot) == original
                db_sync(lambda: Revision.objects.filter(pk=revision.pk).update(status="draft"))
        finally:
            browser.close()
    foreign = Client()
    other = User.objects.create_user(
        username="foreign-photo-edit",
        email="foreign@example.invalid",
        email_verified_at=timezone.now(),
    )
    for acceptance in LegalAcceptance.objects.filter(user=person.individual):
        LegalAcceptance.objects.create(
            user=other, document=acceptance.document, action=acceptance.action
        )
    foreign.force_login(other)
    for action in ["remove", "reorder"]:
        assert (
            foreign.post(
                f"/{language}/photos/{photos[0].pk}/{action}/", {"direction": "up"}
            ).status_code
            == 404
        )
    assert snapshot() == original
    assert (
        client.post(
            f"/{language}/photos/{photos[0].pk}/reorder/", {"direction": "down"}
        ).status_code
        == 302
    )
    assert list(Photo.objects.order_by("position", "created_at").values_list("pk", flat=True)) == [
        photos[1].pk,
        photos[0].pk,
    ]
    assert client.post(f"/{language}/photos/{photos[0].pk}/remove/").status_code == 302
    revision.refresh_from_db()
    photos[0].refresh_from_db()
    assert revision.edit_version == before + 2 and photos[0].removed_at
    assert Photo.objects.filter(removed_at__isnull=True).get().pk == photos[1].pk
