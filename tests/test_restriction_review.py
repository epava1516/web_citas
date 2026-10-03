import uuid

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import Client
from test_report_assignment import coordinator
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.lifecycle import act as lifecycle_act
from apps.safety.models import ReportAction, Restriction

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-individual")
    report = case(client, person)
    original, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect evidence supporting preventive restriction"},
    )
    path, data = action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 302
    independent, admin = coordinator()
    independent.user_permissions.add(Permission.objects.get(codename="review_restriction"))
    return report, person, original, staff, independent, admin


def inspect(staff, report):
    assert (
        staff.post(
            f"/en/moderation/reports/{report.pk}/",
            {"purpose": "Independently inspect current case and restriction history"},
        ).status_code
        == 200
    )


def test_independent_lift_requires_fresh_inspection_and_never_republishes(request):
    report, person, _, _, user, staff = prepared(request)
    path, data = action(staff, report, "lift")
    assert staff.post(path, data).status_code == 409
    inspect(staff, report)
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    report.refresh_from_db()
    restriction = Restriction.objects.get(report=report)
    assert report.status == "lifted" and report.version == 4
    assert not restriction.active and restriction.review_action.actor_id == user.pk
    assert restriction.reviewed_at and ReportAction.objects.filter(operation="lift").count() == 1
    listing = person.listing
    listing.refresh_from_db()
    assert listing.status == "paused" and listing.available_until is None
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 404
    lifecycle_act(person.individual, listing.pk, uuid.uuid4(), listing.lifecycle_version, "resume")
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 200


def test_original_decider_cannot_review_and_changed_manager_rejects_old_form(request):
    report, person, original, first, _, staff = prepared(request)
    original.user_permissions.add(Permission.objects.get(codename="review_restriction"))
    inspect(first, report)
    path, data = action(first, report, "lift")
    assert first.post(path, data).status_code == 403
    inspect(staff, report)
    path, data = action(staff, report, "lift")
    Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version + 1)
    assert staff.post(path, data).status_code == 409
    assert Restriction.objects.get(report=report).active
    assert not ReportAction.objects.filter(operation="lift").exists()


def test_uphold_preserves_block_and_same_reviewer_cannot_reconsider_it(request):
    report, person, _, _, _, staff = prepared(request)
    assert report.pk in [
        item.pk for item in staff.get("/en/moderation/reports/").context["reports"]
    ]
    inspect(staff, report)
    path, data = action(staff, report, "uphold")
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    report.refresh_from_db()
    assert report.status == "upheld" and Restriction.objects.get(report=report).active
    inspect(staff, report)
    path, data = action(staff, report, "lift")
    assert staff.post(path, data).status_code == 403
    person.listing.refresh_from_db()
    with pytest.raises(ValidationError, match="Restriction"):
        lifecycle_act(
            person.individual,
            person.listing.pk,
            uuid.uuid4(),
            person.listing.lifecycle_version,
            "resume",
        )


def test_lifting_one_case_does_not_release_other_active_restrictions(request):
    report, person, _, first, _, staff = prepared(request)
    second = case(Client())
    path, data = action(first, second, "claim")
    first.post(path, data)
    inspect(first, second)
    path, data = action(first, second, "link", link_listing_id=person.listing.pk)
    assert first.post(path, data).status_code == 302
    path, data = action(first, second, "restrict")
    assert first.post(path, data).status_code == 302
    inspect(staff, report)
    path, data = action(staff, report, "lift")
    assert staff.post(path, data).status_code == 302
    assert Restriction.objects.filter(active=True).count() == 1
    assert Restriction.objects.get(report=second).active
    person.listing.refresh_from_db()
    with pytest.raises(ValidationError, match="Restriction"):
        lifecycle_act(
            person.individual,
            person.listing.pk,
            uuid.uuid4(),
            person.listing.lifecycle_version,
            "resume",
        )


def test_mobile_independent_reviewer_lifts_without_publication(
    live_server, request, settings, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    from apps.core.models import User

    settings.DEBUG = True
    report, person, _, _, _, _ = prepared(request)
    editor = User.objects.get(username="fixture-v1-editor")
    editor.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_report", "review_restriction"])
    )
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["editor"]
    path = f"/en/moderation/reports/{report.pk}/"
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
            page.goto(live_server.url + "/en/moderation/reports/")
            page.get_by_role("link", name="Inspect report", exact=True).click()
            page.locator("[name=purpose]").fill(
                "Independently read current restriction and evidence"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(page.get_by_role("heading", name="Case history", exact=True)).to_be_visible()
            page.get_by_role("link", name="Case actions", exact=True).click()
            page.locator("[name=operation]").select_option("lift")
            page.locator("[name=reason]").fill(
                "Independent synthetic review supports lifting restriction without automatic republication"
            )
            page.get_by_role("button", name="Record case action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private report inspection", exact=True)
            ).to_be_visible()
            page.reload()
            assert "lifted" in page.content()
            visitor = browser.new_page()
            assert visitor.goto(live_server.url + public_path).status == 404
            page.goto(live_server.url + path)
            expect(page.get_by_role("heading", name="Case history", exact=True)).to_have_count(0)
        finally:
            browser.close()
    restriction = Restriction.objects.get(report=report)
    assert not restriction.active and restriction.review_action.actor_id == editor.pk
    person.listing.refresh_from_db()
    assert person.listing.status == "paused"


def test_concurrent_independent_reviews_create_only_one_outcome(request):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    from apps.core.models import User
    from apps.safety.decisions import act

    report, person, _, _, independent, staff = prepared(request)
    editor = User.objects.get(username="fixture-v1-editor")
    editor.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_report", "review_restriction"])
    )
    second = Client()
    second.force_login(editor)
    session = second.session
    session["mfa_version"] = editor.mfa_version
    session.save()
    inspect(staff, report)
    inspect(second, report)
    revision_id = person.listing.approved_revision_id
    barrier = Barrier(2)

    def review(operation):
        close_old_connections()
        try:
            user = User.objects.get(pk=independent.pk if operation == "lift" else editor.pk)
            barrier.wait(timeout=10)
            try:
                act(
                    user,
                    report.pk,
                    uuid.uuid4(),
                    3,
                    operation,
                    "Independent reason for concurrent restriction review",
                    manager_version=person.manager_version,
                    revision_id=revision_id,
                )
                return operation
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(review, ["lift", "uphold"]))
    assert outcomes.count(None) == 1
    report.refresh_from_db()
    restriction = Restriction.objects.get(report=report)
    winner = next(value for value in outcomes if value)
    assert report.version == 4
    assert report.status == ("lifted" if winner == "lift" else "upheld")
    assert restriction.active == (winner == "uphold")
    assert restriction.review_action.operation == winner
    assert restriction.review_action.expected_version == 3
    assert ReportAction.objects.filter(report=report).count() == 3
    person.listing.refresh_from_db()
    assert person.listing.status == "paused"


def test_general_report_permission_does_not_grant_independent_review(request):
    report, _, _, _, independent, staff = prepared(request)
    independent.user_permissions.remove(Permission.objects.get(codename="review_restriction"))
    assert report.pk not in [
        item.pk for item in staff.get("/en/moderation/reports/").context["reports"]
    ]
    inspect(staff, report)
    path, data = action(staff, report, "lift")
    assert staff.post(path, data).status_code == 403
    assert Restriction.objects.get(report=report).active
    assert not ReportAction.objects.filter(operation="lift").exists()
