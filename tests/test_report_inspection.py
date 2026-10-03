import json
import shutil

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, payload, photo_environment  # noqa: F401

from apps.core.models import AgencyMember, Person, User
from apps.safety.models import Report, ReportAccess

pytestmark = pytest.mark.django_db(transaction=True)


def reviewer():
    user = User.objects.get(username="fixture-v1-moderator")
    user.user_permissions.add(Permission.objects.get(codename="review_report"))
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return user, client


def case(client, person=None):
    target = (
        client.get(f"/en/listing/{person.listing.pk}/").context["report_target"] if person else ""
    )
    assert (
        client.post(
            "/en/safety/report/",
            payload(
                client, target=target, email="private@example.invalid", name="Private notifier"
            ),
        ).status_code
        == 302
    )
    return Report.objects.latest("created_at")


def test_sensitive_data_requires_explicit_audited_access_and_valid_purpose(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    path = f"/en/moderation/reports/{report.pk}/"
    response = staff.get(path)
    assert response.status_code == 200 and b"private@example.invalid" not in response.content
    assert not ReportAccess.objects.exists()
    assert staff.post(path, {"purpose": "short"}).status_code == 400
    assert not ReportAccess.objects.exists()
    response = staff.post(path, {"purpose": "Review evidence for this private report"})
    assert response.status_code == 200 and b"private@example.invalid" in response.content
    assert response["Cache-Control"] == "private, no-store"
    access = ReportAccess.objects.get()
    assert access.actor_id == user.pk and access.report_id == report.pk
    assert b"private@example.invalid" not in staff.get(path).content
    assert Client().get(path).status_code == 302
    Report.objects.filter(pk=report.pk).update(actor=user)
    assert staff.post(path, {"purpose": "Review evidence for my own report"}).status_code == 403
    assert ReportAccess.objects.count() == 1


def test_original_agency_and_revoked_editor_cannot_inspect_after_transfer(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    report = case(client, person)
    agency = person.agency
    assert (
        report.reported_agency_id == agency.pk and report.reported_subject_id == person.subject_id
    )
    person.agency = None
    person.individual = person.subject
    person.assigned_editor = None
    person.manager_version += 1
    person.save()
    AgencyMember.objects.filter(agency=agency).update(active=False)
    for user in [agency.owner, User.objects.get(username="fixture-v1-editor"), person.subject]:
        user.user_permissions.add(Permission.objects.get(codename="review_report"))
        user.mfa_enabled = True
        user.mfa_version = 1
        user.save(update_fields=["mfa_enabled", "mfa_version"])
        staff = Client()
        staff.force_login(user)
        session = staff.session
        session["mfa_version"] = 1
        session.save()
        assert staff.get(f"/en/moderation/reports/{report.pk}/").status_code == 403
        assert not staff.get("/en/moderation/reports/").context["reports"]
    assert not ReportAccess.objects.exists()


def test_mobile_moderator_inspection_requires_reason_then_hides_on_get(
    live_server, request, settings, tmp_path
):
    settings.DEBUG = True
    client = request.getfixturevalue("directory")
    report = case(client)
    reviewer()
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    path = f"/en/moderation/reports/{report.pk}/"
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
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.goto(live_server.url + path)
            assert "private@example.invalid" not in page.content()
            page.locator("[name=purpose]").fill("Inspect evidence for this synthetic report")
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_be_visible()
            expect(page.get_by_text("private@example.invalid", exact=False)).to_be_visible()
            page.goto(live_server.url + path)
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_have_count(0)
        finally:
            browser.close()
    assert ReportAccess.objects.filter(report=report).count() == 1


def test_transfer_between_initial_check_and_lock_does_not_expose_payload(request, monkeypatch):
    from apps.safety import views

    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    report = case(client, person)
    user, staff = reviewer()
    original = views.permitted
    changed = False

    def interleaved_check(actor, candidate):
        nonlocal changed
        allowed = original(actor, candidate)
        if not changed:
            changed = True
            Person.objects.filter(pk=person.pk).update(
                agency=None, individual=user, assigned_editor=None
            )
        return allowed

    monkeypatch.setattr(views, "permitted", interleaved_check)
    response = staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Review evidence during management change"},
    )
    assert response.status_code == 409
    assert b"private@example.invalid" not in response.content
    assert not ReportAccess.objects.exists()


@pytest.mark.parametrize("failure", ["permission", "disabled_mfa", "stale_mfa"])
def test_inspection_denies_missing_permission_or_current_mfa(request, failure):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    if failure == "permission":
        user.user_permissions.clear()
    elif failure == "disabled_mfa":
        User.objects.filter(pk=user.pk).update(mfa_enabled=False)
    else:
        session = staff.session
        session["mfa_version"] = user.mfa_version - 1
        session.save()
    response = staff.post(
        f"/en/moderation/reports/{report.pk}/", {"purpose": "Inspect restricted evidence"}
    )
    if failure == "permission":
        assert response.status_code == 403
    else:
        assert response.status_code == 302
        assert response.url == (
            "/en/account/mfa/enroll/" if failure == "disabled_mfa" else "/en/account/mfa/"
        )
    assert b"private@example.invalid" not in response.content
    assert not ReportAccess.objects.exists()
