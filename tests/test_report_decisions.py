import uuid

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.lifecycle import act as lifecycle_act
from apps.listings.models import Listing
from apps.listings.submissions import validate_submission
from apps.safety.models import ReportAction, Restriction

pytestmark = pytest.mark.django_db(transaction=True)


def action(staff, report, operation, **changes):
    path = f"/en/moderation/reports/{report.pk}/decision/"
    data = {
        key: value
        for key, value in staff.get(path).context["form"].initial.items()
        if value is not None
    }
    data.update(
        operation=operation, reason="Review of synthetic evidence supports this action", **changes
    )
    return path, data


def test_restriction_removes_publication_and_cannot_be_bypassed_by_lifecycle(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-individual")
    listing = person.listing
    photo = listing.approved_revision.photos.first()
    photo_path = f"/en/listing/{listing.pk}/photo/{photo.pk}/"
    assert Client().get(photo_path).status_code == 200
    report = case(client, person)
    _, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    assert (
        staff.post(
            f"/en/moderation/reports/{report.pk}/",
            {"purpose": "Inspect evidence before deciding restriction"},
        ).status_code
        == 200
    )
    path, data = action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    assert Restriction.objects.count() == 1 and ReportAction.objects.count() == 2
    listing.refresh_from_db()
    assert listing.status == "paused" and listing.available_until is None
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 404
    assert Client().get(photo_path).status_code == 404
    for operation in ["resume", "renew", "available"]:
        with pytest.raises(ValidationError, match="Restriction"):
            lifecycle_act(
                person.individual,
                listing.pk,
                uuid.uuid4(),
                listing.lifecycle_version,
                operation,
                True,
            )
    with pytest.raises(ValidationError, match="Restriction"):
        validate_submission(listing.approved_revision, person)
    Listing.objects.filter(pk=listing.pk).update(status="published")
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 404
    assert Client().get(photo_path).status_code == 404
    results = Client().get("/en/").context["page"]
    assert results.paginator.count == 1
    assert listing.pk not in [item.pk for item in results.object_list]
    assert (
        "Review of synthetic evidence"
        not in ReportAction.objects.get(operation="restrict").encrypted_reason
    )


def test_decision_requires_assignment_inspection_and_current_publication(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-individual")
    report = case(client, person)
    _, staff = reviewer()
    path, data = action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 409
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    path, data = action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 409
    staff.post(
        f"/en/moderation/reports/{report.pk}/", {"purpose": "Inspect supporting synthetic evidence"}
    )
    Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
    assert staff.post(path, data).status_code == 409
    assert not Restriction.objects.exists()
    assert ReportAction.objects.count() == 1


def test_unlinked_report_cannot_restrict_and_replay_cannot_change_outcome(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    _, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect exact reference and explanation"},
    )
    path, data = action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 409
    path, data = action(staff, report, "dismiss")
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    data["reason"] = "Changed private reason for the same action key"
    assert staff.post(path, data).status_code == 409
    report.refresh_from_db()
    assert report.status == "dismissed" and report.version == 3
    assert ReportAction.objects.count() == 2 and not Restriction.objects.exists()


def test_concurrent_claims_only_assign_one_moderator(request):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.contrib.auth.models import Permission
    from django.db import close_old_connections, connections

    from apps.core.models import User
    from apps.safety.decisions import act

    client = request.getfixturevalue("directory")
    report = case(client)
    first, _ = reviewer()
    second = User.objects.get(username="fixture-v1-visitor")
    second.mfa_enabled = True
    second.save(update_fields=["mfa_enabled"])
    second.user_permissions.add(Permission.objects.get(codename="review_report"))
    barrier = Barrier(2)

    def claim(actor_id):
        close_old_connections()
        try:
            actor = User.objects.get(pk=actor_id)
            barrier.wait(timeout=10)
            try:
                act(
                    actor,
                    report.pk,
                    uuid.uuid4(),
                    1,
                    "claim",
                    "Assign synthetic case for evidence review",
                )
                return actor_id
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(claim, [first.pk, second.pk]))
    report.refresh_from_db()
    assert outcomes.count(None) == 1
    assert report.assigned_to_id in [value for value in outcomes if value]
    assert report.version == 2 and ReportAction.objects.count() == 1


def test_mobile_moderator_assigns_inspects_and_restricts(live_server, request, settings, tmp_path):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-individual")
    report = case(client, person)
    reviewer()
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    report_path = f"/en/moderation/reports/{report.pk}/"
    public_path = f"/en/listing/{person.listing.pk}/"
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
            page.goto(live_server.url + report_path)
            page.get_by_role("link", name="Case actions", exact=True).click()
            page.locator("[name=operation]").select_option("claim")
            page.locator("[name=reason]").fill("Assign synthetic case for detailed private review")
            page.get_by_role("button", name="Record case action", exact=True).click()
            page.locator("[name=purpose]").fill("Inspect evidence supporting the synthetic report")
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_be_visible()
            page.get_by_role("link", name="Case actions", exact=True).click()
            page.locator("[name=operation]").select_option("restrict")
            page.locator("[name=reason]").fill(
                "Synthetic evidence supports preventive restriction pending independent review"
            )
            page.get_by_role("button", name="Record case action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private report inspection", exact=True)
            ).to_be_visible()
            page.reload()
            assert "restricted" in page.content()
            assert "private@example.invalid" not in page.content()
            visitor = browser.new_page()
            assert visitor.goto(live_server.url + public_path).status == 404
        finally:
            browser.close()
    assert Restriction.objects.count() == 1 and ReportAction.objects.count() == 2


def test_same_action_key_racing_across_cases_is_conflict_not_partial_assignment(
    request, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    from apps.core.models import User
    from apps.safety.decisions import act
    from apps.safety.models import Report

    client = request.getfixturevalue("directory")
    reports = [case(client), case(client)]
    user, _ = reviewer()
    key = uuid.uuid4()
    barrier = Barrier(2)
    original_create = ReportAction.objects.create

    def racing_create(**kwargs):
        barrier.wait(timeout=10)
        return original_create(**kwargs)

    monkeypatch.setattr(ReportAction.objects, "create", racing_create)

    def claim(report_id):
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            try:
                act(
                    actor,
                    report_id,
                    key,
                    1,
                    "claim",
                    "Claim synthetic case with colliding request key",
                )
                return "accepted"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(claim, [report.pk for report in reports]))
    assert sorted(outcomes) == ["accepted", "conflict"]
    assert ReportAction.objects.count() == 1
    assert Report.objects.filter(status="reviewing", version=2, assigned_to=user).count() == 1
    assert (
        Report.objects.filter(status="received", version=1, assigned_to__isnull=True).count() == 1
    )
