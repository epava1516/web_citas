import json
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_complaint_assignment import action, coordinator, prepared
from test_complaint_linking import decision as report_decision
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AgencyMember, Person, User
from apps.listings.models import ModerationDecision
from apps.listings.moderation import decide
from apps.safety.complaint_actions import act
from apps.safety.models import ComplaintAction

pytestmark = pytest.mark.django_db(transaction=True)


def test_rejected_listing_decision_can_be_linked_without_reopening_review(request):
    complaint, moderator, _, _ = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-model-b")
    revision = person.listing.revisions.get(status="pending")
    decide(
        moderator,
        revision.pk,
        revision.edit_version,
        "rejected",
        "Synthetic rejected review, not a real person",
    )
    target = ModerationDecision.objects.get(revision=revision)
    independent = staff_for(User.objects.get(username="fixture-v1-visitor"))
    path, data = linking(independent, complaint, target)
    assert independent.post(path, data).status_code == 302
    revision.refresh_from_db()
    person.listing.refresh_from_db()
    complaint.refresh_from_db()
    assert complaint.listing_decision_id == target.pk
    assert revision.status == "rejected" and person.listing.status == "rejected"
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 404


def staff_for(user):
    user.mfa_enabled = True
    user.mfa_version = 1
    user.save(update_fields=["mfa_enabled", "mfa_version"])
    user.user_permissions.add(Permission.objects.get(codename="review_complaint"))
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return client


def linking(staff, complaint, target):
    path, data = action(staff, complaint, "claim")
    assert staff.post(path, data).status_code == 302
    assert (
        staff.post(
            f"/en/moderation/complaints/{complaint.pk}/",
            {"purpose": "Read reference before linking historical revision decision"},
        ).status_code
        == 200
    )
    path, data = action(staff, complaint, "link_listing")
    return path, data | {
        "decision_id": target.pk,
        "decision_case_version": target.revision.edit_version,
    }


def test_listing_decision_link_is_versioned_private_and_does_not_republish(request):
    complaint, _, _, receipt = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    target = ModerationDecision.objects.get(revision=person.listing.approved_revision)
    _, staff = coordinator()
    path, data = linking(staff, complaint, target)
    assert staff.post(path, data | {"decision_case_version": 999}).status_code == 409
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    complaint.refresh_from_db()
    assert complaint.listing_decision_id == target.pk and complaint.decision_id is None
    assert complaint.listing_decision_subject_id == person.subject_id and complaint.version == 3
    assert ComplaintAction.objects.filter(operation="link_listing").count() == 1
    body = Client().get(receipt).content
    assert target.reason.encode() not in body and str(target.revision_id).encode() not in body
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 200
    original = staff_for(target.reviewer)
    assert original.get(f"/en/moderation/complaints/{complaint.pk}/").status_code == 403


def test_historical_agency_and_revoked_editor_remain_excluded_after_transfer(request):
    complaint, _, _, _ = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    target = ModerationDecision.objects.get(revision=person.listing.approved_revision)
    agency = person.agency
    person.agency = None
    person.individual = person.subject
    person.assigned_editor = None
    person.manager_version += 1
    person.save()
    AgencyMember.objects.filter(agency=agency).update(active=False)
    independent = staff_for(User.objects.get(username="fixture-v1-visitor"))
    path, data = linking(independent, complaint, target)
    assert independent.post(path, data).status_code == 302
    for user in [agency.owner, User.objects.get(username="fixture-v1-editor"), person.subject]:
        staff = staff_for(user)
        assert staff.get(f"/en/moderation/complaints/{complaint.pk}/").status_code == 403
        assert staff.post(path, data).status_code == 403
        assert not staff.get("/en/moderation/complaints/").context["complaints"]


def test_unknown_historical_publisher_fails_closed_and_original_reviewer_cannot_link(request):
    complaint, _, original, _ = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    target = ModerationDecision.objects.get(revision=person.listing.approved_revision)
    path, data = linking(original, complaint, target)
    assert original.post(path, data).status_code == 403
    complaint.refresh_from_db()
    assert complaint.listing_decision_id is None and complaint.version == 2
    _, independent = coordinator()
    # Recover the already claimed case through the authorized coordinator route.
    path, data = action(independent, complaint, "unassign")
    assert independent.post(path, data).status_code == 302
    target.revision.publisher_acceptance = None
    target.revision.save(update_fields=["publisher_acceptance"])
    path, data = linking(independent, complaint, target)
    assert independent.post(path, data).status_code == 403
    complaint.refresh_from_db()
    assert complaint.listing_decision_id is None and complaint.version == 4


def test_mobile_listing_link_survives_reload_without_public_disclosure(
    live_server, request, settings, tmp_path
):
    settings.DEBUG = True
    complaint, _, _, receipt = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    target = ModerationDecision.objects.get(revision=person.listing.approved_revision)
    revision_version = target.revision.edit_version
    coordinator()
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["agency"]
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
            page.get_by_role("link", name="Private review requests", exact=True).click()
            page.get_by_role("link", name="Inspect review request", exact=True).click()
            page.get_by_role("link", name="Request actions", exact=True).click()
            page.locator("[name=operation]").select_option("claim")
            page.locator("[name=reason]").fill("Acquire independent synthetic listing complaint")
            page.get_by_role("button", name="Record request action", exact=True).click()
            page.locator("[name=purpose]").fill(
                "Inspect request before linking listing review decision"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_be_visible()
            page.get_by_role("link", name="Request actions", exact=True).click()
            page.locator("[name=operation]").select_option("link_listing")
            page.locator("[name=decision_id]").fill(str(target.pk))
            page.locator("[name=decision_case_version]").fill(str(revision_version))
            page.locator("[name=reason]").fill(
                "The reference identifies this exact listing revision decision"
            )
            page.get_by_role("button", name="Record request action", exact=True).click()
            expect(page.locator(f'[data-linked-listing-decision="{target.pk}"]')).to_be_visible()
            page.reload()
            expect(page.locator(f'[data-linked-listing-decision="{target.pk}"]')).to_be_visible()
            anonymous = browser.new_page()
            anonymous.goto(live_server.url + receipt)
            assert target.reason not in anonymous.content()
            assert str(target.revision_id) not in anonymous.content()
        finally:
            browser.close()


def test_racing_report_and_listing_links_cannot_attach_two_sources(request):
    complaint, _, _, _ = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    listing_target = ModerationDecision.objects.get(revision=person.listing.approved_revision)
    report_target, report, _, _ = report_decision(request)
    owner, staff = coordinator()
    linking(staff, complaint, listing_target)
    choices = [
        ("link_listing", listing_target.pk, listing_target.revision.edit_version),
        ("link", report_target.pk, report.version),
    ]
    barrier = Barrier(2)

    def link(choice):
        close_old_connections()
        try:
            user = User.objects.get(pk=owner.pk)
            barrier.wait(timeout=10)
            operation, target_id, source_version = choice
            try:
                act(
                    user,
                    complaint.pk,
                    uuid.uuid4(),
                    2,
                    operation,
                    "Concurrent choice of exact synthetic decision source",
                    target_id,
                    source_version,
                )
                return "ok"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(link, choice) for choice in choices]
        assert sorted(job.result() for job in jobs) == ["conflict", "ok"]
    complaint.refresh_from_db()
    assert complaint.version == 3
    assert bool(complaint.decision_id) != bool(complaint.listing_decision_id)
    assert ComplaintAction.objects.exclude(operation="claim").count() == 1
