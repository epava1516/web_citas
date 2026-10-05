import uuid

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

from apps.listings.models import Revision
from apps.safety.models import RightsAction, RightsExportPreview
from apps.safety.rights_copy_inspection import inspect_page
from apps.safety.rights_exports import generate

pytestmark = pytest.mark.django_db(transaction=True)


def test_page_inspection_is_audited_replayable_and_not_full_preview(request, settings):
    case, actor, _, _, _, person = prepared(request, settings)
    Revision.objects.bulk_create(
        [
            Revision(
                listing=person.listing, manager_version=person.manager_version, title=f"History {n}"
            )
            for n in range(24)
        ]
    )
    key = uuid.uuid4()
    first = inspect_page(actor, case.pk, case.version, key, "Review synthetic revision page")
    assert len(first["entries"]) == 10 and first["has_next"] and first["inspection_only"]
    replay = inspect_page(actor, case.pk, case.version, key, "Review synthetic revision page")
    assert replay["entries"] == first["entries"]
    assert RightsAction.objects.filter(operation="copy_page_read").count() == 1
    second = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid.uuid4(),
        "Review next revision page",
        page=2,
        cursor=first["cursor"],
    )
    assert not {r["revision"] for r in first["entries"]} & {
        r["revision"] for r in second["entries"]
    }
    third = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid.uuid4(),
        "Review final revision page",
        page=3,
        cursor=second["cursor"],
    )
    assert len(third["entries"]) == 5 and not third["has_next"]
    assert not RightsExportPreview.objects.filter(request=case).exists()
    with pytest.raises(ValidationError, match="Preview current"):
        generate(
            actor,
            case.pk,
            uuid.uuid4(),
            case.version,
            "Attempt delivery from partial inspection",
            first,
        )
    before = RightsAction.objects.filter(operation="copy_page_read").count()
    person.listing.revisions.filter(title="History 0").update(title="Changed after page inspection")
    with pytest.raises(ValidationError, match="source changed"):
        inspect_page(
            actor,
            case.pk,
            case.version,
            uuid.uuid4(),
            "Inspect obsolete next page",
            page=2,
            cursor=first["cursor"],
        )
    assert RightsAction.objects.filter(operation="copy_page_read").count() == before


def test_http_page_inspection_hides_data_on_get_and_validates_continuation(request, settings):
    case, actor, staff, _, _, person = prepared(request, settings)
    revision = person.listing.revisions.first()
    revision.description = "PRIVATE_PAGED_DESCRIPTION"
    revision.save(update_fields=["description"])
    path = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    page = staff.get(path)
    assert page.status_code == 200 and b"PRIVATE_PAGED_DESCRIPTION" not in page.content
    response = staff.post(
        path,
        {
            "key": uuid.uuid4(),
            "version": case.version,
            "operation": "inspect_page",
            "section": "revisions",
            "page": 1,
            "purpose": "Read paginated source through private form",
        },
    )
    assert response.status_code == 200 and b"PRIVATE_PAGED_DESCRIPTION" in response.content
    assert "no-store" in response["Cache-Control"]
    assert b"Section inspection only" in response.content
    assert b"PRIVATE_PAGED_DESCRIPTION" not in staff.get(path).content
    assert not RightsExportPreview.objects.filter(request=case).exists()
    response = staff.post(
        path,
        {
            "key": uuid.uuid4(),
            "version": case.version,
            "operation": "inspect_page",
            "section": "revisions",
            "page": 2,
            "purpose": "Attempt continuation without signed cursor",
        },
    )
    assert response.status_code == 409
    cursor = inspect_page(
        actor, case.pk, case.version, uuid.uuid4(), "Read bound revision inspection source"
    )["cursor"]
    with pytest.raises(ValidationError):
        inspect_page(
            actor,
            case.pk,
            case.version,
            uuid.uuid4(),
            "Attempt different section with cursor",
            section="favorites",
            cursor=cursor,
        )
    with pytest.raises(ValidationError):
        inspect_page(
            actor,
            case.pk,
            case.version,
            uuid.uuid4(),
            "Attempt modified cursor payload",
            cursor=cursor + "x",
        )


def test_sections_deliver_only_subject_records_and_paginate_acceptances(request, settings):
    from apps.core.models import (
        LegalAcceptance,
        LegalDocument,
        RepresentationAction,
        VerificationCheck,
    )
    from apps.listings.models import Favorite

    case, actor, _, _, _, person = prepared(request, settings)
    document = LegalDocument.objects.first()
    for n in range(11):
        LegalAcceptance.objects.create(
            user=person.subject, document=document, action=f"paged-own-{n}"
        )
    LegalAcceptance.objects.create(
        user=person.agency.owner, document=document, action="FOREIGN_ACCEPTANCE"
    )
    own_favorite, _ = Favorite.objects.get_or_create(user=person.subject, listing=person.listing)
    Favorite.objects.get_or_create(user=person.agency.owner, listing=person.listing)
    VerificationCheck.objects.create(
        person=person,
        subject=person.subject,
        manager_version=person.manager_version,
        provider="own-check",
    )
    VerificationCheck.objects.create(
        person=person,
        subject=person.agency.owner,
        manager_version=person.manager_version,
        provider="FOREIGN_CHECK",
    )
    RepresentationAction.objects.create(
        person=person,
        subject=person.subject,
        manager_version=person.manager_version,
        action="own-history",
    )
    RepresentationAction.objects.create(
        person=person,
        subject=person.agency.owner,
        manager_version=person.manager_version,
        action="FOREIGN_HISTORY",
    )
    first = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid.uuid4(),
        "Inspect legal acceptance history section",
        section="legal_acceptances",
    )
    rows = first["entries"]
    page = first
    while page["has_next"]:
        page = inspect_page(
            actor,
            case.pk,
            case.version,
            uuid.uuid4(),
            "Inspect next legal acceptance section",
            section="legal_acceptances",
            page=page["page"] + 1,
            cursor=page["cursor"],
        )
        rows += page["entries"]
    assert len(rows) == LegalAcceptance.objects.filter(user=person.subject).count()
    assert "FOREIGN_ACCEPTANCE" not in str(rows)
    result = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid.uuid4(),
        "Inspect subject favorite activity section",
        section="favorites",
    )
    assert result["entries"] == [
        {
            "listing_reference": str(own_favorite.listing_id),
            "created_at": own_favorite.created_at.isoformat(),
        }
    ]
    result = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid.uuid4(),
        "Inspect scoped subject verification section",
        section="verifications",
    )
    assert "own-check" in str(result["entries"]) and "FOREIGN_CHECK" not in str(result)
    result = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid.uuid4(),
        "Inspect scoped representation history",
        section="representation_history",
    )
    assert "own-history" in str(result["entries"]) and "FOREIGN_HISTORY" not in str(result)


@pytest.mark.parametrize("change", ["session", "mfa", "expiry", "proof", "permission"])
def test_inspection_cursor_and_authority_revalidated_without_new_audit(
    request, settings, monkeypatch, change
):
    from django.core import signing
    from django.core.exceptions import PermissionDenied

    from apps.core.models import User

    case, actor, _, _, _, _ = prepared(request, settings)
    first = inspect_page(
        actor, case.pk, case.version, uuid.uuid4(), "Inspect source before authority changes"
    )
    if change in {"session", "mfa"}:
        field = "session_version" if change == "session" else "mfa_version"
        User.objects.filter(pk=actor.pk).update(**{field: getattr(actor, field) + 1})
    elif change == "expiry":
        now = signing.time.time()
        monkeypatch.setattr(signing.time, "time", lambda: now + 7200)
    elif change == "proof":
        case.proofs.update(status="failed")
    else:
        actor.user_permissions.clear()
    before = RightsAction.objects.filter(operation="copy_page_read").count()
    with pytest.raises((PermissionDenied, ValidationError)):
        inspect_page(
            actor,
            case.pk,
            case.version,
            uuid.uuid4(),
            "Attempt obsolete inspection continuation",
            cursor=first["cursor"],
        )
    assert RightsAction.objects.filter(operation="copy_page_read").count() == before
    assert not RightsExportPreview.objects.filter(request=case).exists()


def test_permission_removed_during_source_read_rolls_back_inspection_audit(
    request, settings, monkeypatch
):
    from django.core.exceptions import PermissionDenied

    from apps.safety import rights_copy_inspection

    case, actor, _, _, _, _ = prepared(request, settings)
    original = rights_copy_inspection.source_copy

    def revoke(*args):
        result = original(*args)
        actor.user_permissions.clear()
        return result

    monkeypatch.setattr(rights_copy_inspection, "source_copy", revoke)
    with pytest.raises(PermissionDenied):
        inspect_page(
            actor, case.pk, case.version, uuid.uuid4(), "Inspect while authority is revoked"
        )
    assert not RightsAction.objects.filter(operation="copy_page_read").exists()


@pytest.mark.parametrize("language", ["en", "es"])
def test_mobile_page_inspection_login_next_replay_and_clean_get(
    live_server, request, settings, tmp_path, language
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, _, person = prepared(request, settings)
    Revision.objects.bulk_create(
        [
            Revision(
                listing=person.listing,
                manager_version=person.manager_version,
                description="PRIVATE_PAGE_TEXT_" + "x" * 600,
                title=f"Synthetic mobile history {n}",
            )
            for n in range(23)
        ]
    )
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
    path = f"/{language}/moderation/rights/{case.pk}/export/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(moderator["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(moderator["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            page.goto(live_server.url + path)
            assert "PRIVATE_PAGE_TEXT_" not in page.content()
            page.locator("[name=operation]").select_option("inspect_page")
            page.locator("[name=section]").select_option("revisions")
            page.locator("[name=purpose]").fill(
                "Inspect first source page on synthetic mobile session"
            )
            page.get_by_role(
                "button",
                name="Record copy action" if english else "Registrar acción de copia",
                exact=True,
            ).click()
            expect(page.locator("#inspection-page-output")).to_contain_text("PRIVATE_PAGE_TEXT_")
            next_label = "Inspect next page" if english else "Consultar página siguiente"
            next_form = page.locator("form").filter(
                has=page.get_by_role("button", name=next_label, exact=True)
            )
            next_form.locator("[name=purpose]").fill(
                "Inspect second source page on synthetic mobile session"
            )
            next_form.get_by_role("button", name=next_label, exact=True).click()
            expect(
                page.get_by_role(
                    "heading",
                    name=("Section inspection only:" if english else "Solo consulta de sección:"),
                )
            ).to_contain_text("2")
            page.reload()
            expect(page.locator("#inspection-page-output")).to_contain_text("PRIVATE_PAGE_TEXT_")
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            save_label = "Save page decisions" if english else "Guardar decisiones de página"
            save_form = page.locator("form").filter(
                has=page.get_by_role("button", name=save_label, exact=True)
            )
            entries = json.loads(save_form.locator("[name=entries]").input_value())
            entries[0]["description"] = "PRIVATE_SAVED_MOBILE_TEXT"
            save_form.locator("[name=entries]").fill(json.dumps(entries))
            save_form.locator("[name=reason]").fill("Review saved decisions on mobile device")
            save_form.get_by_role("button", name=save_label, exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("revisions")
            import re

            reference = re.search(
                r"(\d+) · revisions", page.get_by_role("status").inner_text()
            ).group(1)
            assert "PRIVATE_SAVED_MOBILE_TEXT" not in page.content()
            page.reload()
            expect(page.get_by_role("status")).to_contain_text("revisions")
            assert "PRIVATE_SAVED_MOBILE_TEXT" not in page.content()
            page.goto(live_server.url + path)
            assert "PRIVATE_PAGE_TEXT_" not in page.content()
            assert "PRIVATE_SAVED_MOBILE_TEXT" not in page.content()
            page.locator("[name=operation]").select_option("inspect_saved_page")
            page.locator("[name=review_id]").fill(reference)
            page.locator("[name=purpose]").fill("Inspect saved page decisions on mobile device")
            page.get_by_role(
                "button",
                name="Record copy action" if english else "Registrar acción de copia",
                exact=True,
            ).click()
            expect(page.locator("#saved-page-output")).to_contain_text("PRIVATE_SAVED_MOBILE_TEXT")
            page.reload()
            expect(page.locator("#saved-page-output")).to_contain_text("PRIVATE_SAVED_MOBILE_TEXT")
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.goto(live_server.url + path)
            assert "PRIVATE_SAVED_MOBILE_TEXT" not in page.content()
        finally:
            browser.close()
    assert RightsAction.objects.filter(request=case, operation="copy_page_read").count() == 2
    assert RightsAction.objects.filter(request=case, operation="copy_page_save").count() == 1
    assert RightsAction.objects.filter(request=case, operation="copy_review_read").count() == 1
    assert not RightsExportPreview.objects.filter(request=case).exists()


def test_global_key_constraint_conflict_is_controlled_after_stale_lookup(
    request, settings, monkeypatch
):
    case, actor, _, _, _, _ = prepared(request, settings)
    key = uuid.uuid4()
    inspect_page(actor, case.pk, case.version, key, "Record initial synthetic inspection")
    original_filter = RightsAction.objects.filter

    def stale_filter(*args, **kwargs):
        query = original_filter(*args, **kwargs)
        if kwargs == {"key": key}:
            query.first = lambda: None
        return query

    monkeypatch.setattr(RightsAction.objects, "filter", stale_filter)
    with pytest.raises(ValidationError, match="Conflicting inspection key"):
        inspect_page(actor, case.pk, case.version, key, "Record conflicting synthetic inspection")
    assert original_filter(key=key).count() == 1
    assert not RightsExportPreview.objects.filter(request=case).exists()
