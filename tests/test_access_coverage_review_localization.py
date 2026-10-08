"""Audited coverage review language does not alter accounting or authority."""

import shutil
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccessCoverageReview, RightsAction
from apps.safety.rights import fingerprint
from apps.safety.rights_access_coverage import UNPROJECTED
from apps.safety.rights_access_coverage_store import required_references, save
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical, generate, preview
from apps.safety.rights_portability_selection import row_reference

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic coverage review with exact unchanged references"
RAW = "Synthetic / untranslated declaration awaiting independent validation"


def prepare_fixture(request, settings, monkeypatch, account_only):
    case, author, staff, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    author.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    author = User.objects.get(pk=author.pk)
    source = preview(author, case.pk, case.version, REASON)
    export = generate(
        author, case.pk, uuid4(), case.version, REASON, source, information_review_id=decision.pk
    )
    delivered = unseal(export.encrypted_payload)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(Permission.objects.get(codename="verify_rights_scope"))
    reviewer = User.objects.get(pk=reviewer.pk)
    client = operator(reviewer)
    fresh(case, author, staff, reviewer, client)
    declarations = {
        "sections": {
            section: [
                {"row": row_reference(section, i, row), "delivered_index": i, "decisions": {}}
                for i, row in enumerate(project(source))
            ]
            for section, project in SECTIONS.items()
        },
        "boundaries": {
            name: {
                "status": "excluded",
                "reason": RAW,
                "evidence": "Synthetic referenced information review, not legal approval",
            }
            for name in set(source["pending_review"])
            | set(delivered["pending_review"])
            | UNPROJECTED
        },
    }
    action = decision.action
    snapshot = {
        "action": action.pk,
        "request": str(action.request_id),
        "actor": action.actor_id,
        "version": action.expected_version,
        "operation": action.operation,
        "payload": action.payload_digest,
        "reason_ciphertext": fingerprint(action.encrypted_reason),
    }
    refs = {
        label: {"action": action.pk, "digest": fingerprint(canonical(snapshot))}
        for label in required_references(declarations)
    }
    row = save(
        author,
        case.pk,
        case.version,
        case.response_version,
        export.pk,
        uuid4(),
        REASON,
        delivered,
        declarations,
        refs,
        fingerprint(canonical(source)),
        fingerprint(canonical(delivered)),
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    client = operator(reviewer)
    from test_rights_verification import read

    read(client, case)
    return case, author, staff, reviewer, client, row


def captions(page, language):
    expect(page.locator('label[for="id_reason"]')).to_have_text(
        ("Private purpose" if language == "en" else "Motivo privado") + ":"
    )
    expect(page.locator('label[for="decision_reason"]')).to_have_text(
        ("Private purpose" if language == "en" else "Motivo privado") + ":"
    )
    expect(page.locator('label[for="decision_outcome"]')).to_have_text(
        ("Decision" if language == "en" else "Decisión") + ":"
    )
    expect(page.locator('#decision_outcome option[value="approved"]')).to_have_text(
        "Approve" if language == "en" else "Aprobar"
    )
    expect(page.locator('#decision_outcome option[value="rejected"]')).to_have_text(
        "Reject" if language == "en" else "Rechazar"
    )


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_native_coverage_review_private_and_current(
    request, settings, monkeypatch, live_server, language, account_only
):
    settings.DEBUG = True
    case, author, staff, reviewer, client, row = prepare_fixture(
        request, settings, monkeypatch, account_only
    )
    before = (case.version, case.response_version, case.status, row.encrypted_coverage)
    path = f"/{language}/moderation/rights/{case.pk}/access/coverage/{row.pk}/review/"
    # Exact route is resolved before accepting any denial evidence.
    from django.urls import reverse
    from django.utils import translation

    with translation.override(language):
        path = reverse("rights_access_coverage_review", args=[case.pk, row.pk])
    assert client.get(path).status_code == 200
    same = staff.get(path)
    assert same.status_code == 403
    assert same.content.decode() == (
        "Independent reviewer required"
        if language == "en"
        else "Se requiere revisión independiente"
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
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
            page.goto(live_server.url + path)
            captions(page, language)
            assert RAW not in page.content()
            page.locator("#id_reason").fill("short")
            page.locator("form").first.evaluate("(form) => form.noValidate = true")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                page.get_by_role(
                    "button",
                    name="Inspect coverage" if language == "en" else "Consultar cobertura",
                    exact=True,
                ).click()
            assert response.value.status == 400
            captions(page, language)
            assert RAW not in page.content()
            assert (
                db_sync(
                    lambda: RightsAction.objects.filter(
                        request=case, operation="access_cover_read"
                    ).count()
                )
                == 0
            )
            page.locator("#id_reason").fill(REASON)
            page.get_by_role(
                "button",
                name="Inspect coverage" if language == "en" else "Consultar cobertura",
                exact=True,
            ).click()
            expect(page.locator("body")).to_contain_text(RAW)
            captions(page, language)
            assert (
                db_sync(
                    lambda: RightsAction.objects.filter(
                        request=case, operation="access_cover_read"
                    ).count()
                )
                == 1
            )
            page.locator("#decision_reason").fill(REASON)
            page.locator("#decision_outcome").select_option("approved")
            page.get_by_role(
                "button",
                name="Record coverage decision"
                if language == "en"
                else "Registrar decisión de cobertura",
                exact=True,
            ).click()
            expect(page.locator('[role="status"]')).to_contain_text("approved")
            captions(page, language)
            page.goto(live_server.url + path)
            page.reload()
            assert RAW not in page.content()
            assert (
                db_sync(
                    lambda: RightsAccessCoverageReview.objects.filter(
                        coverage=row, outcome="approved"
                    ).count()
                )
                == 1
            )
            db_sync(
                lambda: reviewer.user_permissions.remove(
                    Permission.objects.get(codename="respond_rights_request")
                )
            )
            response = page.goto(live_server.url + path)
            assert response.status == 403
            assert page.locator("body").inner_text() == (
                "Forbidden" if language == "en" else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
        finally:
            browser.close()
    case.refresh_from_db()
    row.refresh_from_db()
    assert (case.version, case.response_version, case.status, row.encrypted_coverage) == before
