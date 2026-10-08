"""Chromium mobile independent complete coverage approval, synthetic facts."""

import shutil
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import Permission
from django.db import transaction
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_coverage_review_localization import captions
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability_export_races import prepared_selection

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsExport, RightsPortabilityCoverageReview
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
    author_client = Client()
    author_client.force_login(author)
    author_session = author_client.session
    author_session["mfa_version"] = author.mfa_version
    author_session.save()
    author_cookie = author_client.cookies[django_settings.SESSION_COOKIE_NAME].value
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
            captions(page, language)
            page.locator("#id_reason").fill("short")
            page.locator("form").first.evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as invalid_read:
                page.get_by_role(
                    "button",
                    name="Inspect coverage page" if english else "Consultar página de cobertura",
                    exact=True,
                ).click()
            assert invalid_read.value.status == 400
            captions(page, language)
            assert page.locator("article").count() == 0
            page.locator("#decision_reason").fill("short")
            page.locator("form").last.evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as invalid_decision:
                page.get_by_role(
                    "button",
                    name="Record coverage decision"
                    if english
                    else "Registrar decisión de cobertura",
                    exact=True,
                ).click()
            assert invalid_decision.value.status == 400
            captions(page, language)
            assert (
                db_sync(
                    lambda: RightsPortabilityCoverageReview.objects.filter(
                        coverage=coverage
                    ).count()
                )
                == 0
            )
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
            captions(page, language)
            assert (
                db_sync(
                    lambda: RightsPortabilityCoverageReview.objects.filter(
                        coverage=coverage
                    ).count()
                )
                == 0
            )
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
                captions(page, language)
                assert "Sí / Yes" not in page.content()
                for article in page.locator("article").all():
                    assert article.locator("p").nth(1).inner_text() in (
                        ["Included", "Excluded", "Pending"]
                        if english
                        else ["Incluido", "Excluido", "Pendiente"]
                    )
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
            page.reload()
            captions(page, language)
            assert "PRIVATE_MOBILE_INDEPENDENT_COVERAGE_FACTS" not in page.content()
            assert page.locator("article").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            # Continue as author in a distinct authenticated browser context.
            author_context = browser.new_context(viewport={"width": 390, "height": 844})
            author_context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": author_cookie,
                        "url": live_server.url,
                    }
                ]
            )
            delivery_page = author_context.new_page()
            delivery_page.goto(inspect_url + "portability/export/")
            expect(
                delivery_page.get_by_role(
                    "heading",
                    name="Deliver approved portable fields"
                    if english
                    else "Entregar campos de portabilidad aprobados",
                    exact=True,
                )
            ).to_be_visible()
            assert "PRIVATE_MOBILE_INDEPENDENT_COVERAGE_FACTS" not in delivery_page.content()
            delivery_page.locator("[name=review]").select_option(str(selected_review.pk))
            delivery_page.locator("[name=coverage_review]").select_option(
                label=f"{coverage.pk} · {coverage.version}"
            )
            delivery_page.locator("[name=reason]").fill(
                "Deliver complete approved synthetic coverage through mobile UI"
            )
            delivery_page.get_by_role(
                "button",
                name="Create approved private copy" if english else "Crear copia privada aprobada",
                exact=True,
            ).click()
            expect(delivery_page.get_by_role("status")).to_contain_text(
                "Private copy created" if english else "Copia privada creada"
            )
            assert "PRIVATE_MOBILE_INDEPENDENT_COVERAGE_FACTS" not in delivery_page.content()
            assert delivery_page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            page.goto(review_url)
            csrf = page.locator("[name=csrfmiddlewaretoken]").first.input_value()
            db_sync(
                lambda: reviewer.user_permissions.remove(
                    Permission.objects.get(codename="review_portability")
                )
            )
            response = page.goto(review_url)
            assert response.status == 403 and page.locator("body").inner_text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = context.request.post(review_url, form={"csrfmiddlewaretoken": csrf})
            assert response.status == 403 and response.text() == (
                "Forbidden" if english else "Acceso denegado"
            )
        finally:
            browser.close()
    decision = RightsPortabilityCoverageReview.objects.get(coverage=coverage)
    assert decision.outcome == "approved" and len(decision.read_ids) == len(pages)
    export = RightsExport.objects.get(action__request=case)
    assert export.portability_binding.coverage_review_id == decision.pk
    payload = unseal(export.encrypted_payload)
    assert payload["export_schema"] == "covered-portability-v1" and payload["partial"] is False
    assert payload["pending_review"] == ["final_response"] and payload["simulation"] is True
    case.refresh_from_db()
    assert case.version == original[0] + 1
    assert (case.status, case.initial_due_at) == original[1:]
