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
from test_complaint_intake import payload as complaint_payload
from test_complaint_linking import decision as report_decision
from test_complaint_listing_linking import linking, staff_for
from test_drafts import contacts
from test_report_decisions import action as report_action
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import ModerationDecision, Revision
from apps.listings.moderation import decide
from apps.safety.complaint_resolutions import resolve
from apps.safety.crypto import unseal
from apps.safety.models import (
    Complaint,
    ComplaintAction,
    ComplaintNotice,
    ComplaintResolution,
    ReportAction,
    Restriction,
)

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Private internal independent resolution rationale"
RESPONSE = "Tras evaluar la documentación disponible, procede una nueva revisión de la decisión. La publicación continúa sujeta a los controles habituales."


def permissions(user):
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "resolve_complaint",
                "review_listing",
                "review_report",
                "review_restriction",
            ]
        )
    )


def inspection(staff, complaint, images=True):
    response = staff.post(
        f"/en/moderation/complaints/{complaint.pk}/",
        {"purpose": "Read current request and linked evidence before independent resolution"},
    )
    if images and response.status_code == 200:
        for photo in response.context["source_photos"]:
            delivered = staff.get(f"/en/moderation/complaints/{complaint.pk}/photo/{photo.pk}/")
            assert delivered.status_code == 200
            assert b"".join(delivered.streaming_content).startswith(b"RIFF")
            delivered.close()
    return response


def resolution(staff, complaint, **changes):
    path = f"/en/moderation/complaints/{complaint.pk}/resolve/"
    data = staff.get(path).context["form"].initial | {
        "outcome": "reconsidered",
        "reason": REASON,
        "response": RESPONSE,
        "redaction_confirmed": True,
    }
    return path, data | changes


def listing_case(request, rejected=False):
    complaint, original, _, receipt = prepared(request)
    person = Person.objects.get(
        subject__username="fixture-v1-model-b" if rejected else "fixture-v1-individual"
    )
    if rejected:
        revision = person.listing.revisions.get(status="pending")
        decide(
            original,
            revision.pk,
            revision.edit_version,
            "rejected",
            "Synthetic original rejection, not a real person",
        )
        user = User.objects.get(username="fixture-v1-visitor")
        staff = staff_for(user)
    else:
        revision = person.listing.approved_revision
        user, staff = coordinator()
    target = ModerationDecision.objects.get(revision=revision)
    permissions(user)
    path, data = linking(staff, complaint, target)
    assert staff.post(path, data).status_code == 302
    return complaint, person, target, user, staff, receipt


@pytest.mark.parametrize("rejected", [False, True])
def test_reconsider_listing_reopens_review_without_publication_and_retry_is_exact(
    request, rejected
):
    complaint, person, target, _, staff, receipt = listing_case(request, rejected)
    original_version = target.revision.edit_version
    assert inspection(staff, complaint).status_code == 200
    path, data = resolution(staff, complaint)
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    complaint.refresh_from_db()
    target.revision.refresh_from_db()
    person.listing.refresh_from_db()
    assert complaint.status == "resolved" and complaint.version == 4
    assert target.revision.status == "pending" and person.listing.status == "pending"
    assert target.revision.edit_version == original_version + 1
    assert (
        not person.listing.approved_revision_id
        and not target.revision.photos.filter(approved=True).exists()
    )
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 404
    item = ComplaintResolution.objects.get()
    assert unseal(item.encrypted_response)["response"] == RESPONSE
    assert RESPONSE not in item.encrypted_response
    body = Client().get(receipt).content
    assert RESPONSE.encode() in body and REASON.encode() not in body
    assert target.reason.encode() not in body
    assert ComplaintAction.objects.filter(operation="resolve").count() == 1
    with pytest.raises(ValidationError, match="Review changed"):
        decide(
            target.reviewer,
            target.revision_id,
            original_version,
            "approved",
            "Stale original moderation form must not approve a reopened revision",
        )
    notice = ComplaintNotice.objects.get()
    assert notice.status == "queued"
    notice_payload = unseal(notice.encrypted_payload)
    assert notice_payload["recipient"] == "own-channel@example.invalid"
    assert REASON not in notice.encrypted_payload and RESPONSE not in notice_payload["body"]
    # A real subsequent moderation decision is still required to expose the revision.
    decide(
        target.reviewer,
        target.revision_id,
        target.revision.edit_version,
        "approved",
        "Synthetic follow-up independently authorized publication checks",
    )
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 200


def report_case(request):
    complaint, _, _, receipt = prepared(request)
    target, report, _, _ = report_decision(request)
    user, staff = coordinator()
    permissions(user)
    path, data = action(staff, complaint, "claim")
    assert staff.post(path, data).status_code == 302
    inspection(staff, complaint)
    path, data = action(staff, complaint, "link")
    assert (
        staff.post(
            path, data | {"decision_id": target.pk, "decision_case_version": report.version}
        ).status_code
        == 302
    )
    inspection(staff, complaint)
    assert (
        staff.post(
            f"/en/moderation/reports/{report.pk}/",
            {
                "purpose": "Read original current report evidence before independent complaint decision"
            },
        ).status_code
        == 200
    )
    return complaint, report, user, staff, receipt


@pytest.mark.parametrize("outcome", ["upheld", "reconsidered"])
def test_report_resolution_uses_independent_restriction_review_without_republication(
    request, outcome
):
    complaint, report, _, staff, receipt = report_case(request)
    path, data = resolution(staff, complaint, outcome=outcome)
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    report.refresh_from_db()
    assert report.status == ("upheld" if outcome == "upheld" else "lifted")
    assert Restriction.objects.get(report=report).active == (outcome == "upheld")
    assert Client().get(f"/en/listing/{report.listing_id}/").status_code == 404
    assert REASON.encode() not in Client().get(receipt).content
    assert ComplaintResolution.objects.count() == 1
    assert (
        ReportAction.objects.filter(
            report=report, operation="lift" if outcome == "reconsidered" else "uphold"
        ).count()
        == 1
    )


def test_resolution_requires_new_evidence_separate_permission_and_redaction(request):
    complaint, person, target, user, staff, _ = listing_case(request)
    path, data = resolution(staff, complaint)
    assert staff.post(path, data).status_code == 409  # Link invalidated the intake read.
    inspection(staff, complaint)
    assert staff.post(path, data | {"redaction_confirmed": False}).status_code == 400
    assert (
        staff.post(
            path, data | {"response": RESPONSE + " Contact private@example.invalid"}
        ).status_code
        == 409
    )
    user.user_permissions.remove(Permission.objects.get(codename="resolve_complaint"))
    assert staff.post(path, data).status_code == 403
    permissions(user)
    target.revision.edit_version += 1
    target.revision.save(update_fields=["edit_version"])
    assert staff.post(path, data).status_code == 409
    assert not ComplaintResolution.objects.exists()
    person.listing.refresh_from_db()
    assert person.listing.status == "published"


def test_resolution_rejects_notifier_identity_and_concurrency_changes_source_once(request):
    complaint, report, user, staff, _ = report_case(request)
    path, data = resolution(staff, complaint)
    assert staff.post(path, data | {"response": RESPONSE + " Private notifier"}).status_code == 409
    barrier = Barrier(2)

    def complete():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                resolve(
                    actor,
                    complaint.pk,
                    uuid.uuid4(),
                    data["version"],
                    data["source_version"],
                    data["outcome"],
                    REASON,
                    RESPONSE,
                    True,
                )
                return "ok"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(complete) for _ in range(2)]
        assert sorted(job.result() for job in jobs) == ["conflict", "ok"]
    assert ComplaintResolution.objects.count() == 1
    assert ReportAction.objects.filter(report=report, operation="lift").count() == 1


def test_lifted_report_can_be_reopened_and_restricted_again_with_preserved_action_history(request):
    complaint, report, _, first, _ = report_case(request)
    path, data = resolution(first, complaint)
    assert first.post(path, data).status_code == 302
    report.refresh_from_db()
    lift = ReportAction.objects.get(report=report, operation="lift")
    public = Client()
    public.post("/en/safety/complaints/", complaint_payload(public))
    second_case = Complaint.objects.exclude(pk=complaint.pk).get()
    user = User.objects.get(username="fixture-v1-visitor")
    second = staff_for(user)
    permissions(user)
    path, data = action(second, second_case, "claim")
    assert second.post(path, data).status_code == 302
    inspection(second, second_case)
    path, data = action(second, second_case, "link")
    assert (
        second.post(
            path, data | {"decision_id": lift.pk, "decision_case_version": report.version}
        ).status_code
        == 302
    )
    inspection(second, second_case)
    second.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect lifted original report for independent reopening"},
    )
    path, data = resolution(second, second_case)
    assert second.post(path, data).status_code == 302
    assert second.post(path, data).status_code == 302
    report.refresh_from_db()
    assert report.status == "received" and report.assigned_to_id is None
    assert ReportAction.objects.filter(report=report, operation="reopen").count() == 1
    path, data = report_action(second, report, "claim")
    assert second.post(path, data).status_code == 302
    second.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect newly assigned report before fresh restriction"},
    )
    path, data = report_action(second, report, "restrict")
    assert second.post(path, data).status_code == 302
    restriction = Restriction.objects.get(report=report)
    assert restriction.active and restriction.review_action_id is None
    assert ReportAction.objects.filter(report=report, operation="restrict").count() == 2
    assert ReportAction.objects.filter(pk=lift.pk).exists()


def test_mobile_motivated_listing_resolution_and_anonymous_response(
    live_server, request, settings, tmp_path
):
    settings.DEBUG = True
    complaint, person, _, _, _, receipt = listing_case(request)
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
            page.locator("[name=purpose]").fill(
                "Read current linked review evidence before independent response"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_role("heading", name="Linked review evidence", exact=True)
            ).to_be_visible()
            page.wait_for_function(
                "() => { const images = Array.from(document.querySelectorAll('img[alt=\"Linked revision photograph\"]')); return images.length > 0 && images.every(image => image.complete && image.naturalWidth > 0); }"
            )
            page.get_by_role("link", name="Resolve review request", exact=True).click()
            page.locator("[name=outcome]").select_option("reconsidered")
            page.locator("[name=reason]").fill(REASON)
            page.locator("[name=response]").fill(RESPONSE)
            page.locator("[name=redaction_confirmed]").check()
            page.get_by_role("button", name="Record resolution", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private decision review intake", exact=True)
            ).to_be_visible()
            page.reload()
            anonymous = browser.new_page()
            anonymous.goto(live_server.url + receipt)
            expect(
                anonymous.get_by_role("heading", name="Review response", exact=True)
            ).to_be_visible()
            expect(anonymous.get_by_text(RESPONSE, exact=True)).to_be_visible()
            anonymous.reload()
            assert REASON not in anonymous.content()
        finally:
            browser.close()
    complaint.refresh_from_db()
    assert complaint.status == "resolved"
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 404


def test_rejected_photos_require_current_private_access_and_foreign_images_are_hidden(request):
    complaint, person, target, _, staff, _ = listing_case(request, rejected=True)
    photo = target.revision.photos.get()
    path = f"/en/moderation/complaints/{complaint.pk}/photo/{photo.pk}/"
    assert staff.get(path).status_code == 409
    assert Client().get(path).status_code == 302
    inspection(staff, complaint, images=False)
    resolution_path, data = resolution(staff, complaint)
    assert staff.post(resolution_path, data).status_code == 409
    foreign = Person.objects.get(
        subject__username="fixture-v1-model-a"
    ).listing.approved_revision.photos.get()
    assert (
        staff.get(f"/en/moderation/complaints/{complaint.pk}/photo/{foreign.pk}/").status_code
        == 404
    )
    response = staff.get(path)
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content).startswith(b"RIFF")
    response.close()
    original = staff_for(target.reviewer)
    assert original.get(path).status_code == 403
    assert staff.post(resolution_path, data).status_code == 302
    person.listing.refresh_from_db()
    assert person.listing.status == "pending"


def test_reopening_rejected_update_preserves_the_existing_public_version(request):
    complaint, moderator, _, _ = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    baseline = person.listing.approved_revision
    owner = Client()
    owner.force_login(person.individual)
    assert owner.post(f"/en/person/{person.pk}/listing/start/").status_code == 302
    revision = Revision.objects.get(listing=person.listing, status="draft")
    assert owner.post(f"/en/draft/{revision.pk}/2/", contacts(revision)).status_code == 302
    revision.refresh_from_db()
    assert (
        owner.post(
            f"/en/draft/{revision.pk}/submit/",
            {"edit_version": revision.edit_version, "declaration": "on"},
        ).status_code
        == 302
    )
    decide(
        moderator,
        revision.pk,
        revision.edit_version,
        "rejected",
        "The synthetic update requires another human review",
    )
    target = ModerationDecision.objects.get(revision=revision)
    user, staff = coordinator()
    permissions(user)
    path, data = linking(staff, complaint, target)
    assert staff.post(path, data).status_code == 302
    inspection(staff, complaint)
    person.listing.refresh_from_db()
    old_lifecycle, old_expiry = person.listing.lifecycle_version, person.listing.expires_at
    path, data = resolution(staff, complaint)
    assert staff.post(path, data).status_code == 302
    person.listing.refresh_from_db()
    revision.refresh_from_db()
    assert revision.status == "pending"
    assert (
        person.listing.status == "published" and person.listing.approved_revision_id == baseline.pk
    )
    assert (
        person.listing.lifecycle_version == old_lifecycle
        and person.listing.expires_at == old_expiry
    )
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 200
