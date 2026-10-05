"""Chromium mobile independent complete coverage approval, synthetic facts."""

import shutil
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.db import transaction
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilityCoverageReview
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_catalog import scalar_fields
from apps.safety.rights_portability_coverage_read_gate import required_pages
from apps.safety.rights_portability_coverage_store import save_coverage
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_mobile_independent_coverage_approval(
    live_server, request, settings, monkeypatch, language, account_only
):
    settings.DEBUG = True
    case, author, selection, selected_review, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    original = case.version, case.status, case.initial_due_at
    facts = {
        "status": "excluded",
        "basis": "other",
        "origin": "inferred",
        "automated": True,
        "subject_related": True,
        "third_party_reviewed": True,
        "reason": "Synthetic fixture exclusion without production factual claim",
        "evidence": "PRIVATE_MOBILE_INDEPENDENT_COVERAGE_FACTS",
    }
    chosen = unseal(selection.encrypted_selection)
    omissions = {name: {} for name in SECTIONS}
    for dataset, reader in SECTIONS.items():
        for index, row in enumerate(reader(source)):
            reference = row_reference(dataset, index, row)
            selected = next(
                (
                    set(item["fields"])
                    for item in chosen["selection"][dataset]
                    if item["row"] == reference
                ),
                set(),
            )
            if any(item["path"] not in selected for item in scalar_fields(row)):
                omissions[dataset][reference] = {"all": facts}
    included = {item["photo"] for item in chosen.get("images", [])}
    images = {
        image["photo"]: facts
        for revision in source["revisions"]
        for image in revision["images"]
        if image["photo"] not in included
    }
    coverage = save_coverage(
        author,
        case.pk,
        case.version,
        selected_review.pk,
        uuid4(),
        0,
        "Prepare complete synthetic coverage before mobile review",
        omissions,
        images,
    )
    reviewer = User.objects.get(pk=selected_review.action.actor_id)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    cookie = client.cookies[django_settings.SESSION_COOKIE_NAME].value
    pages = required_pages(source)
    english = language == "en"
    inspect_url = live_server.url + f"/{language}/moderation/rights/{case.pk}/"
    review_url = inspect_url + f"portability/coverage/{coverage.pk}/review/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(inspect_url)
            page.locator(
                f'a[href="/{language}/moderation/rights/{case.pk}/portability/coverage/{coverage.pk}/review/"]'
            ).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Review portability coverage"
                    if english
                    else "Revisar cobertura de portabilidad",
                    exact=True,
                )
            ).to_be_visible()
            assert "PRIVATE_MOBILE_INDEPENDENT_COVERAGE_FACTS" not in page.content()
            page.locator("#decision_reason").fill(
                "Approve synthetic coverage only after all pages inspected"
            )
            page.get_by_role(
                "button",
                name="Record coverage decision" if english else "Registrar decisión de cobertura",
                exact=True,
            ).click()
            expect(
                page.get_by_text("Inspect every current coverage page before approval", exact=True)
            ).to_be_visible()
            for dataset, index, number, binary in pages:
                page.locator("[name=dataset]").select_option("binary" if binary else dataset)
                page.locator("[name=row_number]").fill(str(index + 1))
                page.locator("[name=field_page]").fill(str(number))
                page.locator("#id_reason").fill(
                    "Inspect synthetic coverage page before independent approval"
                )
                page.get_by_role(
                    "button",
                    name="Inspect coverage page" if english else "Consultar página de cobertura",
                    exact=True,
                ).click()
                expect(
                    page.get_by_role(
                        "heading",
                        name="Inspected coverage" if english else "Cobertura consultada",
                        exact=True,
                    )
                ).to_be_visible()
            page.locator("#decision_reason").fill(
                "Approve synthetic coverage after all current page readings"
            )
            page.locator("[name=outcome]").select_option("approved")
            page.get_by_role(
                "button",
                name="Record coverage decision" if english else "Registrar decisión de cobertura",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Coverage decision recorded" if english else "Decisión de cobertura registrada"
            )
            page.goto(review_url)
            assert "PRIVATE_MOBILE_INDEPENDENT_COVERAGE_FACTS" not in page.content()
            assert page.locator("article").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    decision = RightsPortabilityCoverageReview.objects.get(coverage=coverage)
    assert decision.outcome == "approved" and len(decision.read_ids) == len(pages)
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
