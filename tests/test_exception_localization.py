"""Synthetic reviewed exception preparation, never a legal decision or authority grant."""

import shutil

import pytest
from django.db import connection
from django.test import Client
from django.urls import reverse
from playwright.sync_api import expect, sync_playwright
from test_processing_plans import REASON
from test_purpose_exception_preparation import prepared_exception
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.crypto import unseal
from apps.safety.models import PurposeExceptionProposal, PurposeRestriction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_account_exception_proposal_preserves_scope_and_restriction(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    case, actor, _, plan, favorite = prepared_exception(request, settings, monkeypatch)
    assert case.account_subject_id
    before = case.version, case.status, case.initial_due_at
    client = Client()
    client.force_login(actor)
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    path = (
        reverse("purpose_exception_prepare", kwargs={"case_id": case.pk, "plan_id": plan.pk})
        .replace("/es/", f"/{language}/", 1)
        .replace("/en/", f"/{language}/", 1)
    )
    english = language == "en"
    basis = "Private synthetic exception grounds requiring independent review"
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
            url = live_server.url + path
            page.goto(url)

            def labels():
                expect(
                    page.get_by_text(
                        (
                            "Reviewed operation scopes"
                            if english
                            else "Ámbitos revisados de la operación"
                        )
                        + ":",
                        exact=True,
                    )
                ).to_be_visible()
                for name, label in {
                    "basis": "Minimized specific grounds"
                    if english
                    else "Fundamento concreto minimizado",
                    "reason": "Minimized reason" if english else "Motivo minimizado",
                }.items():
                    expect(page.locator(f"label[for=id_{name}]")).to_have_text(label + ":")
                expected = [
                    ("account", "Identidad y acceso de cuenta", "Account identity and access"),
                    ("authentication", "Tokens, códigos y sesiones", "Tokens, codes and sessions"),
                    ("account_preferences", "Favoritos propios", "Own favorites"),
                    (
                        "transient_copy",
                        "Contenido de copias transitorias",
                        "Transient copy contents",
                    ),
                ]
                assert page.locator("[name=purposes]").evaluate_all("xs=>xs.map(e=>e.value)") == [
                    value for value, _, _ in expected
                ]
                for value, es, en in expected:
                    expect(
                        page.locator(f"input[name=purposes][value={value}]").locator("..")
                    ).to_have_text(en if english else es)

            labels()
            page.locator("[name=purposes][value=account_preferences]").check()
            page.locator("[name=basis]").fill("short")
            page.locator("[name=reason]").fill(REASON)
            page.locator("form").evaluate("e=>e.noValidate=true")
            button = page.locator("form button[type=submit]")
            with page.expect_response(lambda r: r.request.method == "POST") as r:
                button.click()
            assert r.value.status == 400
            assert db_sync(lambda: PurposeExceptionProposal.objects.count()) == 0
            page.locator("[name=basis]").fill(basis)
            with page.expect_response(lambda r: r.request.method == "POST") as r:
                button.click()
            assert r.value.status == 200
            labels()
            page.goto(url)
            page.reload()
            assert basis not in page.content() and REASON not in page.content()
        finally:
            browser.close()
    proposal = PurposeExceptionProposal.objects.get()
    # The immutable payload is the authority boundary, not its translated captions.
    assert proposal.action.actor_id == actor.pk
    assert (
        PurposeRestriction.objects.get().active
        and favorite.__class__.objects.filter(pk=favorite.pk).exists()
    )
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == before
    assert basis not in proposal.encrypted_scope
    assert unseal(proposal.encrypted_scope)["purposes"] == ["account_preferences"]
