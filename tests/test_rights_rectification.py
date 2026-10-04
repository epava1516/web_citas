import pytest
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.safety.crypto import unseal
from apps.safety.models import RightsRectificationProposal

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Private correction justification after scoped evidence review"


def test_encrypted_rectification_proposal_is_idempotent_without_source_change(
    request, settings, monkeypatch
):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    before = person.alias, revision.title, person.listing.status, person.listing.lifecycle_version
    dates = case.received_at, case.initial_due_at
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    page = staff.get(path)
    assert page.status_code == 200 and page["Cache-Control"] == "private, no-store"
    changes = {"alias": "Synthetic corrected alias", "title": "Synthetic corrected title"}
    assert (
        staff.post(
            path,
            page.context["form"].initial
            | {
                "operation": "preview",
                "purpose": "Inspect current profile fields before correction",
            },
        ).status_code
        == 200
    )
    data = page.context["form"].initial | {
        "operation": "propose",
        "fields": list(changes),
        **changes,
        "reason": REASON,
    }
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data | {"reason": REASON + " changed"}).status_code == 409
    item = RightsRectificationProposal.objects.get()
    assert unseal(item.encrypted_changes) == changes
    assert changes["alias"] not in item.encrypted_changes
    assert changes["alias"].encode() not in staff.get(path).content
    person.refresh_from_db()
    revision.refresh_from_db()
    case.refresh_from_db()
    person.listing.refresh_from_db()
    assert (
        person.alias,
        revision.title,
        person.listing.status,
        person.listing.lifecycle_version,
    ) == before
    assert (case.received_at, case.initial_due_at) == dates
    assert case.status == "reviewing" and case.scope_status == "unverified"
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403


def test_shared_identity_fields_cannot_be_proposed_as_profile_text(request, settings, monkeypatch):
    case, _, staff, _, _, _ = ready(request, settings, monkeypatch, "rectify")
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    assert (
        staff.post(
            path,
            initial
            | {
                "operation": "propose",
                "reason": REASON,
                "fields": ["phone"],
                "phone": "unverified contact",
            },
        ).status_code
        == 400
    )
    assert not RightsRectificationProposal.objects.exists()


def test_source_read_is_required_and_text_change_invalidates_it(request, settings, monkeypatch):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    data = initial | {
        "operation": "propose",
        "fields": ["title"],
        "title": "Corrected synthetic title",
        "reason": REASON,
    }
    assert staff.post(path, data).status_code == 409
    response = staff.post(
        path,
        initial
        | {
            "operation": "preview",
            "purpose": "Audit current revision fields for requested correction",
        },
    )
    assert (
        response.status_code == 200
        and response.context["source_fields"]["title"] == person.listing.approved_revision.title
    )
    assert staff.get(path).context["source_fields"] is None
    revision = person.listing.approved_revision
    revision.title = "Interleaved synthetic source correction"
    revision.save(update_fields=["title"])
    assert staff.post(path, data).status_code == 409
    assert not RightsRectificationProposal.objects.exists()
    assert (
        staff.post(
            path,
            initial
            | {
                "operation": "preview",
                "purpose": "Reinspect changed revision fields before correction",
            },
        ).status_code
        == 200
    )
    assert staff.post(path, data).status_code == 302


def test_mobile_source_review_and_field_proposal(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, _, person = ready(request, settings, monkeypatch, "rectify")
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    alias_before = person.alias
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
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/")
            page.get_by_role("link", name="Propose data correction", exact=True).click()
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Inspect current scoped source before proposing correction"
            )
            page.get_by_role("button", name="Record correction action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Audited current fields", exact=True)
            ).to_be_visible()
            expect(page.locator("[name=alias]")).to_have_value(alias_before)
            page.locator('[name=fields][value="alias"]').check()
            page.locator("[name=alias]").fill("Synthetic browser correction")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Record correction action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/rectification/")
            expect(page.locator("[name=alias]")).to_have_value("")
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    proposal = RightsRectificationProposal.objects.get()
    assert unseal(proposal.encrypted_changes) == {"alias": "Synthetic browser correction"}
    person.refresh_from_db()
    assert person.alias == alias_before
