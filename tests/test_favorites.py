import shutil
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Favorite

pytestmark = pytest.mark.django_db(transaction=True)


def visitor():
    user = User.objects.get(username="fixture-v1-visitor")
    client = Client()
    client.force_login(user)
    return user, client


def test_favorites_private_idempotent_permissions_and_hidden_content(request):
    request.getfixturevalue("directory")
    user, client = visitor()
    person = Person.objects.get(individual__username="fixture-v1-individual")
    listing = person.listing
    path = f"/en/listing/{listing.pk}/favorite/"
    assert Client().post(path).status_code == 302
    assert client.get(path).status_code == 405
    assert client.post(path).status_code == client.post(path).status_code == 302
    favorite = Favorite.objects.get(user=user)
    page = client.get("/en/favorites/")
    assert listing.approved_revision.title.encode() in page.content
    assert page["Cache-Control"] == "private, no-store"
    other = Client()
    other.force_login(User.objects.get(username="fixture-v1-individual"))
    assert other.post(f"/en/favorites/{favorite.pk}/remove/").status_code == 404
    assert Favorite.objects.count() == 1
    assert listing.approved_revision.title.encode() not in other.get("/en/favorites/").content
    person.consent_revoked_at = timezone.now()
    person.save(update_fields=["consent_revoked_at"])
    page = client.get("/en/favorites/")
    assert b"Listing unavailable" in page.content
    assert listing.approved_revision.title.encode() not in page.content
    assert listing.approved_revision.phone.encode() not in page.content
    assert str(listing.pk).encode() not in page.content
    assert client.post(path).status_code == 404
    assert client.post(f"/en/favorites/{favorite.pk}/remove/").status_code == 302
    assert Favorite.objects.count() == 0
    assert client.post(f"/en/favorites/{favorite.pk}/remove/").status_code == 404


def test_concurrent_favorite_add_is_unique(request):
    request.getfixturevalue("directory")
    user, _ = visitor()
    listing = Person.objects.get(individual__username="fixture-v1-individual").listing
    barrier = Barrier(2)

    def add():
        close_old_connections()
        try:
            client = Client()
            client.force_login(User.objects.get(pk=user.pk))
            barrier.wait(timeout=10)
            return client.post(f"/es/listing/{listing.pk}/favorite/").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(add) for _ in range(2)]
        assert [future.result() for future in futures] == [302, 302]
    assert Favorite.objects.filter(user=user, listing=listing).count() == 1


def test_mobile_visitor_favorite_save_reload_remove(live_server, request, settings):
    settings.DEBUG = True
    request.getfixturevalue("directory")
    listing_id = Person.objects.get(individual__username="fixture-v1-individual").listing.pk
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill("fixture-visitor@example.invalid")
            page.locator("[name=password]").fill("Long-directory-fixture-password!873")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/en/listing/{listing_id}/")
            page.get_by_role("button", name="Save private favorite", exact=True).click()
            expect(
                page.get_by_role("heading", name="Your private favorites", exact=True)
            ).to_be_visible()
            expect(page.get_by_role("button", name="Remove favorite", exact=True)).to_be_visible()
            page.reload()
            page.get_by_role("button", name="Remove favorite", exact=True).click()
            expect(page.get_by_text("You have no favorites yet.", exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_text("You have no favorites yet.", exact=True)).to_be_visible()
        finally:
            browser.close()
