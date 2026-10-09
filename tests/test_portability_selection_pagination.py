"""Selection UI must bound rows and reject approval with unread pages."""

from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from django.db import transaction
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.listings.models import Revision
from apps.safety.crypto import unseal
from apps.safety.rights_exports import reviewer_case, source_copy
from apps.safety.rights_portability_selection import row_reference
from apps.safety.rights_portability_selection_store import save_selection

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independently inspect every selected synthetic revision page"


def paginated_selection(request, settings, monkeypatch):
    original = fixtures.ready

    def with_history(*args, **kwargs):
        result = original(*args, **kwargs)
        person = result[-1]
        Revision.objects.bulk_create([
            Revision(listing=person.listing, manager_version=person.manager_version,
                     title=f"Page history {index}", description=f"Synthetic appointment schedule {index}")
            for index in range(51)
        ])
        return result

    monkeypatch.setattr(fixtures, "ready", with_history)
    case, author, baseline, previous, person, _, _ = fixtures.prepared_selection(
        request, settings, monkeypatch, False
    )
    with transaction.atomic():
        locked, profile, listing = reviewer_case(author, case.pk)
        source = source_copy(profile, listing, locked)
    body = unseal(baseline.encrypted_selection)
    body["selection"]["revisions"] = [
        {"row": row_reference("revisions", index, row), "fields": ["/description"]}
        for index, row in enumerate(source["revisions"])
        if row["title"].startswith("Page history ")
    ]
    row = save_selection(author, case.pk, case.version, baseline.assessment_review_id,
                         uuid4(), baseline.version, REASON, body["selection"],
                         field_evidence=body["field_evidence"])
    reviewer = User.objects.get(pk=previous.action.actor_id)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    return case, row, reviewer, client


@pytest.mark.parametrize("check", ["bounded_rows", "missing_page"])
def test_selection_requires_bounded_complete_pages(request, settings, monkeypatch, check):
    case, row, _, client = paginated_selection(request, settings, monkeypatch)
    path = f"/en/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
    payload = {"key": uuid4(), "version": case.version, "operation": "inspect",
               "reason": REASON, "page": 1}
    response = client.post(path, payload)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    if check == "bounded_rows":
        assert sum(len(item["rows"]) for item in response.context["reviewed_fields"]) == 50
    else:
        decision = client.post(path, payload | {"key": uuid4(), "operation": "review", "outcome": "approved"})
        assert decision.status_code == 409


@pytest.mark.parametrize("language", ["es", "en"])
def test_complete_pages_replay_and_authenticated_page_records(request, settings, monkeypatch, language):
    from apps.safety.models import RightsPortabilitySelectionRead, RightsPortabilitySelectionReview

    case, row, reviewer, client = paginated_selection(request, settings, monkeypatch)
    path = f"/{language}/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
    first = {"key": uuid4(), "version": case.version, "operation": "inspect", "reason": REASON, "page": 1}
    assert client.get(path).context["body"] is None
    response = client.post(path, first)
    assert response.status_code == 200 and response.context["body"]["pagination"] == {"page": 1, "pages": 2, "total": 52, "rows": 50}
    assert client.post(path, first).status_code == 200
    assert RightsPortabilitySelectionRead.objects.filter(selection=row).count() == 1
    assert client.post(path, first | {"page": 2}).status_code == 409
    assert client.post(path, first | {"key": uuid4(), "page": 3}).status_code == 409
    assert client.post(path, first | {"key": uuid4(), "page": 2}).context["body"]["pagination"]["rows"] == 2
    second = RightsPortabilitySelectionRead.objects.filter(selection=row, page_metadata__page=2).get()
    original = dict(second.page_metadata)
    tampered = original | {"digest": "0" * 64}
    RightsPortabilitySelectionRead.objects.filter(pk=second.pk).update(page_metadata=tampered)
    decision = first | {"key": uuid4(), "operation": "review", "outcome": "approved"}
    assert client.post(path, decision).status_code == 409
    RightsPortabilitySelectionRead.objects.filter(pk=second.pk).update(page_metadata=original)
    assert client.post(path, decision).status_code == 200
    assert client.post(path, decision).status_code == 200
    review = RightsPortabilitySelectionReview.objects.get(selection=row)
    assert len(review.page_reads) == 2
    assert set(review.page_reads) == set(RightsPortabilitySelectionRead.objects.filter(selection=row).values_list("pk", flat=True))
    assert review.action.actor_id == reviewer.pk
    RightsPortabilitySelectionReview.objects.filter(pk=review.pk).update(page_reads=review.page_reads[:1])
    assert client.post(path, decision).status_code == 409


@pytest.mark.parametrize("epoch", ["session_version", "mfa_version"])
def test_pages_from_old_epoch_cannot_authorize_new_session(request, settings, monkeypatch, epoch):
    from test_rights_verification import read

    case, row, reviewer, client = paginated_selection(request, settings, monkeypatch)
    path = f"/en/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
    payload = {"key": uuid4(), "version": case.version, "operation": "inspect", "reason": REASON, "page": 1}
    assert client.post(path, payload).status_code == 200
    assert client.post(path, payload | {"key": uuid4(), "page": 2}).status_code == 200
    User.objects.filter(pk=reviewer.pk).update(**{epoch: getattr(reviewer, epoch) + 1})
    reviewer.refresh_from_db()
    client.logout()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session["account_version"] = reviewer.session_version
    session.save()
    read(client, case)
    assert client.post(path, payload | {"key": uuid4(), "operation": "review", "outcome": "approved"}).status_code == 409


def test_page_rejects_illegible_assessment_without_server_error(request, settings, monkeypatch):
    from apps.safety.models import RightsAction, RightsPortabilityAssessment

    case, row, _, client = paginated_selection(request, settings, monkeypatch)
    before = RightsAction.objects.filter(request=case).count()
    RightsPortabilityAssessment.objects.filter(pk=row.assessment_review.assessment_id).update(
        encrypted_assessment="BROKEN-SYNTHETIC-CIPHERTEXT"
    )
    client.raise_request_exception = False
    path = f"/en/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
    response = client.post(path, {"key": uuid4(), "version": case.version, "operation": "inspect",
                                  "reason": REASON, "page": 1})
    assert response.status_code == 409
    assert RightsAction.objects.filter(request=case).count() == before


@pytest.mark.parametrize("language", ["es", "en"])
def test_browser_requires_both_selection_pages(request, settings, monkeypatch, live_server, language):
    import re
    import shutil

    from playwright.sync_api import expect, sync_playwright

    from apps.safety.models import RightsPortabilitySelectionReview

    case, row, _, client = paginated_selection(request, settings, monkeypatch)
    path = f"/{language}/moderation/rights/{case.pk}/portability/selection/{row.pk}/review/"
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which("chromium-browser"),
                                             args=["--no-sandbox"])
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            # Existing synthetic DB-backed MFA session; this test exercises paging, not login/MFA setup.
            context.add_cookies([{"name": settings.SESSION_COOKIE_NAME,
                                  "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                                  "url": live_server.url, "httpOnly": True, "sameSite": "Lax"}])
            page = context.new_page()
            target = live_server.url + path
            response = page.goto(target)
            assert response.status == 200 and "no-store" in response.headers["cache-control"]
            expect(page.locator("article dl")).to_have_count(0)
            operation = "Operation" if english else "Operación"
            reason = "Private reason" if english else "Motivo privado"
            page_label = "Page" if english else "Página"
            outcome = "Outcome" if english else "Resultado"
            button = "Record review action" if english else "Registrar acción de revisión"
            page.get_by_label(re.compile(r"^" + re.escape(page_label) + r":?$")).fill("1")
            page.get_by_label(re.compile(r"^" + re.escape(reason) + r":?$")).fill(REASON)
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.locator("article dl")).to_have_count(50)
            page.get_by_label(re.compile(r"^" + re.escape(operation) + r":?$")).select_option("review")
            page.get_by_label(re.compile(r"^" + re.escape(outcome) + r":?$")).select_option("approved")
            page.get_by_label(re.compile(r"^" + re.escape(reason) + r":?$")).fill(REASON)
            with page.expect_response(lambda response: response.url == target and response.request.method == "POST") as pending:
                page.get_by_role("button", name=button, exact=True).click()
            assert pending.value.status == 409
            expect(page.get_by_text("Inspect every current selection page before deciding" if english else
                                    "Consulta todas las páginas actuales de selección antes de decidir", exact=True)).to_be_visible()
            page.get_by_label(re.compile(r"^" + re.escape(operation) + r":?$")).select_option("inspect")
            page.get_by_label(re.compile(r"^" + re.escape(outcome) + r":?$")).select_option("")
            page.get_by_label(re.compile(r"^" + re.escape(page_label) + r":?$")).fill("2")
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.locator("article dl")).to_have_count(2)
            page.get_by_label(re.compile(r"^" + re.escape(operation) + r":?$")).select_option("review")
            page.get_by_label(re.compile(r"^" + re.escape(outcome) + r":?$")).select_option("approved")
            page.get_by_label(re.compile(r"^" + re.escape(reason) + r":?$")).fill(REASON)
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("Decision recorded" if english else "Decisión registrada")
            expect(page.locator("article dl")).to_have_count(0)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    decision = RightsPortabilitySelectionReview.objects.get(selection=row)
    assert len(decision.page_reads) == 2
