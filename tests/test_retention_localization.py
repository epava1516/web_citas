"""Operational follow-up presentation does not extend retention or authorize erasure."""

import shutil
from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import connection
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_erasure_plans import BASIS, REASON
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_retention_reviews import prepared

from apps.safety.models import RetentionReview, RetentionReviewEvent

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_retention_review_preserves_plan_authority_and_dates(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    case, _, reviewer, client, _, subject, plan, _ = prepared(request, settings, monkeypatch)
    review = RetentionReview.objects.filter(plan=plan).first()
    original = (
        plan.encrypted_decisions,
        plan.review_on,
        case.version,
        case.initial_due_at,
        subject.email,
        subject.session_version,
    )
    # Resolve the canonical route rather than relying on the provisional path spelling.
    from django.urls import reverse

    path = (
        reverse("retention_review", kwargs={"review_id": review.pk})
        .replace("/es/", f"/{language}/", 1)
        .replace("/en/", f"/{language}/", 1)
    )
    english = language == "en"
    next_date = timezone.localdate() + timedelta(days=7)
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
                for name, label in {
                    "operation": "Operation" if english else "Operación",
                    "reason": "Minimized reason" if english else "Motivo minimizado",
                    "next_review_on": "Next operational review, not retention extension"
                    if english
                    else "Próxima revisión operativa, no ampliación de conservación",
                }.items():
                    expect(page.locator(f"label[for=id_{name}]")).to_have_text(label + ":")
                assert page.locator("[name=operation] option").evaluate_all(
                    "xs=>xs.map(e=>[e.value,e.textContent])"
                ) == [
                    ["inspect", "Inspect purpose" if english else "Consultar finalidad"],
                    [
                        "follow_up",
                        "Record review and follow-up"
                        if english
                        else "Registrar revisión y seguimiento",
                    ],
                ]

            labels()
            assert BASIS not in page.content()
            page.locator("[name=reason]").fill("short")
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as r:
                page.get_by_role(
                    "button",
                    name="Record review action" if english else "Registrar acción de revisión",
                    exact=True,
                ).click()
            assert r.value.status == 400
            assert db_sync(lambda: RetentionReviewEvent.objects.count()) == 0
            page.locator("[name=reason]").fill(REASON)
            with page.expect_response(lambda r: r.request.method == "POST") as r:
                page.get_by_role(
                    "button",
                    name="Record review action" if english else "Registrar acción de revisión",
                    exact=True,
                ).click()
            assert r.value.status == 200
            expect(page.get_by_text(BASIS, exact=True)).to_be_visible()
            labels()
            stale = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            page.locator("[name=operation]").select_option("follow_up")
            page.locator("[name=reason]").fill(REASON)
            page.locator("[name=next_review_on]").fill(next_date.isoformat())
            with page.expect_response(lambda r: r.request.method == "POST") as r:
                page.get_by_role(
                    "button",
                    name="Record review action" if english else "Registrar acción de revisión",
                    exact=True,
                ).click()
            assert r.value.status == 200
            labels()
            expect(page.get_by_role("status")).to_contain_text(
                "Follow-up recorded; original plan unchanged"
                if english
                else "Seguimiento registrado; plan original intacto"
            )
            assert (
                page.request.post(
                    url,
                    form=stale
                    | {
                        "key": str(uuid4()),
                        "operation": "follow_up",
                        "reason": REASON,
                        "next_review_on": next_date.isoformat(),
                    },
                ).status
                == 409
            )
            page.reload()
            assert BASIS not in page.content() and REASON not in page.content()
            assert db_sync(
                lambda: list(
                    RetentionReviewEvent.objects.order_by("pk").values_list("operation", flat=True)
                )
            ) == ["inspect", "follow_up"]
            db_sync(lambda: reviewer.user_permissions.clear())
            assert page.goto(url).status == 403
        finally:
            browser.close()
    review.refresh_from_db()
    plan.refresh_from_db()
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (
        review.version == 2
        and review.next_review_on == next_date
        and review.initial_review_on == original[1]
    )
    assert (
        plan.encrypted_decisions,
        plan.review_on,
        case.version,
        case.initial_due_at,
        subject.email,
        subject.session_version,
    ) == original
    assert RetentionReviewEvent.objects.count() == 2
