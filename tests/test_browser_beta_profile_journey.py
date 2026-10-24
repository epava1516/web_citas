"""Synthetic browser journey from pending profile through correction and withdrawal."""

import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from urllib.parse import urlsplit

import pyotp
import pytest
from django.db import close_old_connections, connections
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt
from apps.listings.models import Listing, Revision

pytestmark = pytest.mark.django_db(transaction=True)


def translated(language, es, en):
    return en if language == "en" else es


def review(page, origin, language, revision_id, outcome):
    reason = f"Synthetic {outcome} review for {revision_id}"
    page.goto(f"{origin}/{language}/moderation/listings/{revision_id}/")
    page.locator("[name=outcome]").select_option(outcome)
    page.locator("[name=reason]").fill(reason)
    page.get_by_role("button", name=translated(language, "Registrar decisión", "Record decision")).click()
    expect(page.get_by_text(reason, exact=True)).to_be_visible()
    return reason


def correct_and_submit(page, origin, language, title):
    page.goto(f"{origin}/{language}/account/")
    page.get_by_role("button", name=translated(
        language, "Completar o editar mi perfil", "Complete or edit my profile"
    )).click()
    revision_id = urlsplit(page.url).path.split("/")[3]
    page.locator("[name=title]").fill(title)
    page.locator("[name=profile_type]").select_option("")
    page.locator("[name=show_trans_label]").check()
    save = translated(language, "Guardar y continuar", "Save and continue")
    page.get_by_role("button", name=save).click()
    page.locator("[name=contact_exposure_accepted]").check()
    page.locator("[name=accept_publishing]").check()
    page.get_by_role("button", name=save).click()
    expect(page.get_by_role("img", name=translated(
        language, "Vista previa privada", "Private photo preview"
    ))).to_be_visible()
    page.get_by_role("link", name=translated(language, "Revisar borrador", "Review draft")).click()
    page.locator("[name=declaration]").check()
    page.get_by_role("button", name=translated(language, "Enviar a revisión", "Send for review")).click()
    expect(page.get_by_text(translated(language, "En revisión", "Under review"), exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text(translated(language, "En revisión", "Under review"), exact=True)).to_be_visible()
    return revision_id


def open_renewal_window(listing_id):
    """Only synthetic clock setup; use a real independent database connection."""
    close_old_connections()
    try:
        return Listing.objects.filter(pk=listing_id).update(
            expires_at=timezone.now() + timedelta(days=3)
        )
    finally:
        connections.close_all()


@pytest.mark.parametrize("language,width", [("es", 390), ("en", 390), ("es", 1280), ("en", 1280)])
def test_profile_publish_reject_correct_renew_pause_and_withdraw(
    live_server, request, settings, language, width
):
    settings.DEBUG = True
    person, _, initial, moderator, _ = request.getfixturevalue("pending")
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["mfa_secret_encrypted"])
    origin = live_server.url
    initial_title = initial.title
    owner_email = person.individual.email
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            owner_context = browser.new_context(viewport={"width": width, "height": 900})
            reviewer_context = browser.new_context(viewport={"width": width, "height": 900})
            guest_context = browser.new_context(viewport={"width": width, "height": 900})
            owner, staff, guest = owner_context.new_page(), reviewer_context.new_page(), guest_context.new_page()
            staff.goto(f"{origin}/{language}/account/login/")
            staff.locator("[name=email]").fill(moderator.email)
            staff.locator("[name=password]").fill("Long-moderator-password!847")
            staff.locator("button[type=submit]").click()
            staff.goto(f"{origin}/{language}/moderation/listings/")
            staff.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            staff.locator("button[type=submit]").click()
            review(staff, origin, language, initial.pk, "approved")
            public_url = f"{origin}/{language}/listing/{initial.listing_id}/"
            assert guest.goto(public_url).status == 200
            expect(guest.get_by_role("heading", name=initial_title, exact=True)).to_be_visible()
            owner.goto(f"{origin}/{language}/account/login/")
            owner.locator("[name=email]").fill(owner_email)
            owner.locator("[name=password]").fill("Long-draft-password!847")
            owner.locator("button[type=submit]").click()
            expect(owner.get_by_role("heading", name=translated(language, "Tu cuenta", "Your account"))).to_be_visible()
            proposed = correct_and_submit(owner, origin, language, "Synthetic romantic profile changes")
            guest.goto(public_url)
            expect(guest.get_by_role("heading", name=initial_title, exact=True)).to_be_visible()
            rejection = review(staff, origin, language, proposed, "rejected")
            owner.goto(f"{origin}/{language}/draft/{proposed}/status/")
            expect(owner.get_by_text(rejection, exact=True)).to_be_visible()
            corrected = correct_and_submit(owner, origin, language, "Synthetic corrected romantic profile")
            review(staff, origin, language, corrected, "approved")
            assert guest.goto(public_url).status == 200
            expect(guest.get_by_role("heading", name="Synthetic corrected romantic profile", exact=True)).to_be_visible()
            manage_url = f"{origin}/{language}/listing/{initial.listing_id}/manage/"
            for operation, status_es, status_en, public_status in [
                ("pause", "En pausa", "Paused", 404),
                ("resume", "Publicado", "Published", 200),
            ]:
                owner.goto(manage_url)
                owner.locator("[name=operation]").select_option(operation)
                owner.get_by_role("button", name=translated(language, "Aplicar acción", "Apply action")).click()
                expect(owner.get_by_text(translated(language, status_es, status_en), exact=True)).to_be_visible()
                owner.reload()
                assert guest.goto(public_url).status == public_status
            # Synthetic setup opens the real renewal window without waiting 23 days.
            with ThreadPoolExecutor(max_workers=1) as executor:
                assert executor.submit(open_renewal_window, initial.listing_id).result() == 1
            owner.goto(manage_url)
            owner.locator("[name=operation]").select_option("renew")
            owner.locator("[name=confirm]").check()
            owner.get_by_role("button", name=translated(language, "Aplicar acción", "Apply action")).click()
            expect(owner.get_by_text(translated(language, "Publicado", "Published"), exact=True)).to_be_visible()
            assert guest.goto(public_url).status == 200
            owner.locator("[name=operation]").select_option("withdraw")
            owner.get_by_role("button", name=translated(language, "Aplicar acción", "Apply action")).click()
            expect(owner.get_by_text(translated(language, "Retirado", "Withdrawn"), exact=True)).to_be_visible()
            owner.reload()
            assert guest.goto(public_url).status == 404
        finally:
            browser.close()

    # Read persisted state after Playwright releases its event loop.
    initial.refresh_from_db()
    proposed_revision = Revision.objects.get(pk=proposed)
    corrected_revision = Revision.objects.get(pk=corrected)
    listing = Listing.objects.get(pk=initial.listing_id)
    assert initial.title == initial_title
    assert proposed_revision.status == "rejected" and proposed_revision.profile_type == ""
    assert proposed_revision.show_trans_label and corrected_revision.show_trans_label
    assert corrected_revision.source_revision_id == proposed_revision.pk
    assert corrected_revision.status == "approved" and corrected_revision.profile_type == ""
    assert listing.approved_revision_id == corrected_revision.pk and listing.status == "withdrawn"
    assert listing.expires_at > timezone.now() + timedelta(days=29)
    assert Listing.objects.filter(person=person).count() == 1
