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
    from apps.catalog.models import Municipality

    new_city = (
        Municipality.objects.filter(active=True)
        .exclude(pk=person.listing.approved_revision.municipality_id)
        .first()
    )
    assert new_city
    from django.utils import timezone

    from apps.core.models import PhoneClaim

    replacement_phone = PhoneClaim.objects.create(
        phone="+34600000992",
        agency_id=person.agency_id,
        individual_id=person.individual_id,
        verified_at=timezone.now(),
        verification_procedure="simulator-v1",
    )
    from apps.catalog.models import Category, Service

    new_category = Category.objects.create(
        slug="synthetic-browser-corrected-category",
        name_es="Synthetic browser category",
        name_en="Synthetic browser category",
    )
    new_service = Service.objects.create(
        slug="synthetic-browser-corrected-service",
        category=new_category,
        name_es="Synthetic browser service",
        name_en="Synthetic browser service",
    )
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
            page.locator('[name=fields][value="location"]').check()
            page.locator("[name=municipality]").select_option(str(new_city.pk))
            page.locator("[name=postal_code]").select_option("")
            page.locator("[name=zone]").select_option("")
            page.locator('[name=fields][value="catalog"]').check()
            for field in ["categories", "services"]:
                for checkbox in page.locator(f"[name={field}]").all():
                    checkbox.uncheck()
            page.locator(f'[name=categories][value="{new_category.pk}"]').check()
            page.locator(f'[name=services][value="{new_service.pk}"]').check()
            page.locator('[name=fields][value="rates"]').check()
            for checkbox in page.locator('[name$="-DELETE"]').all():
                checkbox.check()
            page.locator("[name=rates-0-DELETE]").uncheck()
            page.locator("[name=rates-0-concept]").fill("Synthetic browser rate")
            page.locator("[name=rates-0-mode]").select_option("consult")
            page.locator("[name=rates-0-amount]").fill("")
            page.locator("[name=rates-0-duration_minutes]").fill("")
            page.locator('[name=fields][value="contacts"]').check()
            page.locator("[name=phone]").fill(replacement_phone.phone)
            page.locator("[name=whatsapp]").check()
            page.locator("[name=telegram]").fill("synthetic_browser")
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
    assert unseal(proposal.encrypted_changes) == {
        "alias": "Synthetic browser correction",
        "contacts": {
            "phone": replacement_phone.phone,
            "whatsapp": True,
            "telegram": "synthetic_browser",
        },
        "rates": [
            {
                "concept": "Synthetic browser rate",
                "mode": "consult",
                "amount": None,
                "currency": "EUR",
                "duration_minutes": None,
            }
        ],
        "catalog": {"categories": [new_category.pk], "services": [new_service.pk]},
        "location": {"municipality": new_city.pk, "postal_code": None, "zone": None},
    }
    person.refresh_from_db()
    assert person.alias == alias_before


def test_location_form_requires_coherent_public_safe_city_postal_and_zone(
    request, settings, monkeypatch
):
    from apps.catalog.models import Municipality, PostalCode, Zone
    from apps.safety.rectification_location import source as location_source

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    city = revision.municipality
    other = Municipality.objects.filter(active=True).exclude(pk=city.pk).first()
    assert other
    postal = PostalCode.objects.create(code="99982", source=city.source, public_safe=False)
    postal.municipalities.add(city)
    zone = Zone.objects.create(
        code="synthetic-location-test",
        name="Synthetic location test",
        municipality=city,
        source=city.source,
    )
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {"operation": "preview", "purpose": "Inspect current location before scoped correction"},
    )
    assert page.status_code == 200
    assert page.context["source_fields"]["location"] == location_source(revision)
    assert staff.get(path).context["source_fields"] is None
    data = initial | {
        "operation": "propose",
        "fields": ["location"],
        "municipality": other.pk,
        "postal_code": postal.pk,
        "zone": zone.pk,
        "reason": REASON,
    }
    assert staff.post(path, data).status_code == 400  # Restricted precision cannot be selected.
    postal.public_safe = True
    postal.save(update_fields=["public_safe"])
    assert staff.post(path, data).status_code == 400  # CP and area belong to the old city.
    assert staff.post(path, data | {"postal_code": ""}).status_code == 400
    assert (
        staff.post(path, data | {"municipality": "", "postal_code": "", "zone": ""}).status_code
        == 400
    )
    assert not RightsRectificationProposal.objects.exists()
    assert staff.post(path, data | {"postal_code": "", "zone": ""}).status_code == 302
    proposal = RightsRectificationProposal.objects.get()
    assert unseal(proposal.encrypted_changes) == {
        "location": {"municipality": other.pk, "postal_code": None, "zone": None}
    }
    revision.refresh_from_db()
    assert revision.municipality_id == city.pk
    assert staff.get(path).context["source_fields"] is None


def test_catalog_form_requires_active_compatible_categories_and_services(
    request, settings, monkeypatch
):
    from django.core.exceptions import ValidationError

    from apps.catalog.models import Category, Service
    from apps.safety.rectification_catalog import source as catalog_source
    from apps.safety.rectification_catalog import validate

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    original = catalog_source(revision)
    category = Category.objects.create(
        slug="synthetic-catalog-proposal",
        name_es="Synthetic proposal category",
        name_en="Synthetic proposal category",
    )
    service = Service.objects.create(
        slug="synthetic-catalog-proposal",
        category=category,
        name_es="Synthetic proposal service",
        name_en="Synthetic proposal service",
        active=False,
    )
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {"operation": "preview", "purpose": "Inspect current catalog before scoped correction"},
    )
    assert page.status_code == 200 and page.context["source_fields"]["catalog"] == original
    assert staff.get(path).context["source_fields"] is None
    data = initial | {
        "operation": "propose",
        "fields": ["catalog"],
        "categories": [category.pk],
        "services": [service.pk],
        "reason": REASON,
    }
    assert staff.post(path, data).status_code == 400
    service.active = True
    service.save(update_fields=["active"])
    assert staff.post(path, data | {"categories": original["categories"]}).status_code == 400
    assert staff.post(path, data | {"categories": []}).status_code == 400
    assert staff.post(path, data | {"services": []}).status_code == 400
    with pytest.raises(ValidationError):
        validate({"categories": [category.pk, category.pk], "services": [service.pk]})
    with pytest.raises(ValidationError):
        validate({"categories": [True], "services": [service.pk]})
    assert not RightsRectificationProposal.objects.exists()
    assert staff.post(path, data).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "catalog": {"categories": [category.pk], "services": [service.pk]}
    }
    assert catalog_source(revision) == original


@pytest.mark.parametrize("table_mode", ["fixed", "clear", "maximum"])
def test_rate_table_form_validates_management_amount_duration_and_deletion(
    request, settings, monkeypatch, table_mode
):
    from django.core.exceptions import ValidationError

    from apps.safety.rectification_rates import source as rates_source
    from apps.safety.rectification_rates import validate

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    before = rates_source(revision)
    assert before
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {"operation": "preview", "purpose": "Inspect tariff source before complete replacement"},
    )
    assert page.status_code == 200 and page.context["source_fields"]["rates"] == before
    assert staff.get(path).context["source_fields"] is None
    data = initial | {
        "operation": "propose",
        "fields": ["rates"],
        "reason": REASON,
        "rates-TOTAL_FORMS": "1",
        "rates-INITIAL_FORMS": "0",
        "rates-0-concept": "Synthetic corrected tariff",
        "rates-0-mode": "consult",
        "rates-0-amount": "50",
        "rates-0-duration_minutes": "60",
    }
    assert staff.post(path, data).status_code == 409
    assert (
        staff.post(path, data | {"rates-0-mode": "fixed", "rates-0-amount": "0"}).status_code == 409
    )
    assert (
        staff.post(
            path, data | {"rates-0-mode": "fixed", "rates-0-duration_minutes": "10081"}
        ).status_code
        == 409
    )
    assert (
        staff.post(
            path, {key: value for key, value in data.items() if key != "rates-TOTAL_FORMS"}
        ).status_code
        == 409
    )
    assert staff.post(path, data | {"rates-TOTAL_FORMS": "1000000"}).status_code == 409
    assert not RightsRectificationProposal.objects.exists()
    row = {
        "concept": "Synthetic corrected tariff",
        "mode": "fixed",
        "amount": "50.00",
        "currency": "EUR",
        "duration_minutes": 60,
    }
    for invalid in [
        {**row, "currency": "USD"},
        {**row, "amount": 50.0},
        {**row, "duration_minutes": True},
        {**row, "amount": "NaN"},
    ]:
        with pytest.raises(ValidationError):
            validate([invalid])
    valid = data | {"rates-0-mode": "fixed"}
    expected = [row]
    if table_mode == "clear":
        valid["rates-0-DELETE"] = "on"
        expected = []
    elif table_mode == "maximum":
        valid["rates-TOTAL_FORMS"] = "10"
        expected = []
        for index in range(10):
            current = {**row, "concept": f"Synthetic corrected tariff {index}"}
            expected.append(current)
            valid.update(
                {
                    f"rates-{index}-{field}": value
                    for field, value in current.items()
                    if field != "currency"
                }
            )
    assert staff.post(path, valid).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "rates": expected
    }
    assert rates_source(revision) == before


def test_contact_proposal_requires_verified_owner_and_audited_binding(
    request, settings, monkeypatch
):
    from django.utils import timezone

    from apps.core.models import PhoneClaim, User
    from apps.safety.rectification_contacts import source as contacts_source

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    revision = person.listing.approved_revision
    old = contacts_source(revision)
    old_claim = person.phone_claim
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    page = staff.post(
        path,
        initial
        | {"operation": "preview", "purpose": "Inspect current contact and verification binding"},
    )
    assert page.status_code == 200 and page.context["source_fields"]["contacts"] == old
    assert old["phone"].encode() not in staff.get(path).content
    data = initial | {
        "operation": "propose",
        "fields": ["contacts"],
        "phone": "+34600000993",
        "whatsapp": "on",
        "telegram": "synthetic_contact",
        "reason": REASON,
    }
    assert staff.post(path, data).status_code == 409  # No verified claim is invented.
    foreign = PhoneClaim.objects.create(
        phone=data["phone"],
        individual=User.objects.get(username="fixture-v1-visitor"),
        verified_at=timezone.now(),
        verification_procedure="simulator-v1",
    )
    assert staff.post(path, data).status_code == 409
    foreign.delete()  # Synthetic unused record, no user content.
    target = PhoneClaim.objects.create(
        phone=data["phone"],
        agency_id=person.agency_id,
        individual_id=person.individual_id,
        verification_procedure="simulator-v1",
    )
    assert staff.post(path, data).status_code == 409
    target.verified_at = timezone.now()
    target.save(update_fields=["verified_at"])
    assert staff.post(path, data | {"telegram": "invalid/path"}).status_code == 400
    assert staff.post(path, data | {"phone": ""}).status_code == 400
    original_verified = old_claim.verified_at
    old_claim.verified_at = None
    old_claim.save(update_fields=["verified_at"])
    assert staff.post(path, data).status_code == 409  # Source binding changed without case version.
    old_claim.verified_at = original_verified
    old_claim.save(update_fields=["verified_at"])
    assert not RightsRectificationProposal.objects.exists()
    assert staff.post(path, data).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "contacts": {"phone": target.phone, "whatsapp": True, "telegram": "synthetic_contact"}
    }
    person.refresh_from_db()
    assert person.phone_claim_id == old_claim.pk and contacts_source(revision) == old
