import uuid

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import User
from apps.safety.models import RightsRectificationNotification, RightsRectificationReview
from apps.safety.rights_actions import act
from apps.safety.rights_rectification import preview, propose

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic correction assessment with minimized internal grounds"


def independent_case(request, settings, monkeypatch, *, with_receipt=False, changes=None):
    case, original, staff, client, receipt, person = ready(
        request, settings, monkeypatch, "rectify"
    )
    original.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["manage_rights_assignment", "verify_rights_scope", "review_rectification"]
        )
    )
    original = User.objects.get(pk=original.pk)
    if changes:
        source = person.listing.approved_revision
        assert source is not None and source.municipality_id
        # Include a synthetic travel area before proposal, so every relation copy is exercised.
        source.travel_areas.add(source.municipality)
    preview(
        original, case.pk, case.version, "Inspect scoped current fields for correction proposal"
    )
    proposal = propose(
        original,
        case.pk,
        uuid.uuid4(),
        case.version,
        changes or {"alias": "Synthetic reviewed correction"},
        REASON,
    )
    path = f"/en/moderation/rights/{case.pk}/rectification/{proposal.pk}/review/"
    assert staff.get(path).status_code == 403
    case.refresh_from_db()
    act(original, case.pk, uuid.uuid4(), case.version, "unassign", REASON)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["review_rights_request", "execute_rights_request", "review_rectification"]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    case.refresh_from_db()
    act(reviewer, case.pk, uuid.uuid4(), case.version, "claim", REASON)
    fresh(case, reviewer, other, original, staff)
    result = case, reviewer, other, person, proposal, path
    return (*result, client, receipt) if with_receipt else result


@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_independent_audited_review_needs_fresh_source_and_preserves_publication(
    request, settings, monkeypatch, outcome
):
    case, reviewer, other, person, _, path = independent_case(request, settings, monkeypatch)
    data = {
        "key": uuid.uuid4(),
        "version": case.version,
        "operation": "review",
        "outcome": outcome,
        "reason": REASON,
    }
    assert other.post(path, data).status_code == 409
    preview(
        reviewer, case.pk, case.version, "Read unchanged current correction source independently"
    )
    assert other.post(path, data).status_code == 409
    inspected = other.post(
        path,
        {
            "key": uuid.uuid4(),
            "version": case.version,
            "operation": "inspect",
            "purpose": "Read proposed changes before independent correction review",
        },
    )
    assert inspected.status_code == 200 and inspected.context["changes"] == {
        "alias": "Synthetic reviewed correction"
    }
    assert other.get(path).context["changes"] is None
    before = person.alias, person.listing.status, person.listing.lifecycle_version
    assert other.post(path, data).status_code == 302
    assert other.post(path, data).status_code == 302
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert (person.alias, person.listing.status, person.listing.lifecycle_version) == before
    assert RightsRectificationReview.objects.get().outcome == outcome
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_rectification"))
    assert other.post(path, data).status_code == 403


def test_mobile_independent_source_and_proposal_review(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, reviewer, other, person, proposal, path, client, receipt = independent_case(
        request, settings, monkeypatch, with_receipt=True
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    from apps.core.mfa import encrypt

    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.save(update_fields=["mfa_secret_encrypted"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["visitor"]
    alias_before = person.alias
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
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/rectification/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Read current fields before independent proposed correction review"
            )
            page.get_by_role("button", name="Record correction action", exact=True).click()
            page.get_by_role("link", name="Review correction proposal", exact=True).click()
            page.locator("[name=purpose]").fill(
                "Read proposed changes before independent correction decision"
            )
            page.get_by_role("button", name="Record review action", exact=True).click()
            expect(
                page.get_by_text("Profile name: Synthetic reviewed correction", exact=False)
            ).to_be_visible()
            page.locator("[name=operation]").select_option("review")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Record review action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            # Synthetic identity provider only; actual PG proof/read guards and browser MFA.
            from concurrent.futures import ThreadPoolExecutor

            def refresh_verification(confirm=False):
                from django.db import close_old_connections, connections

                close_old_connections()
                try:
                    original = proposal.action.actor
                    staff = Client()
                    staff.force_login(original)
                    session = staff.session
                    session["mfa_version"] = original.mfa_version
                    session.save()
                    if confirm:
                        notification = RightsRectificationNotification.objects.get()
                        assert (
                            client.post(
                                receipt + f"response/{notification.response_id}/acknowledge/",
                                {"received": "yes"},
                            ).status_code
                            == 302
                        )
                    case.refresh_from_db()
                    fresh(case, reviewer, other, original, staff)
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(refresh_verification).result(timeout=30)
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/rectification/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Read current source before communicating approved correction"
            )
            page.get_by_role("button", name="Record correction action", exact=True).click()
            page.get_by_role("link", name="Review correction proposal", exact=True).click()
            page.locator("[name=purpose]").fill("Read approved changes before prior communication")
            page.get_by_role("button", name="Record review action", exact=True).click()
            page.locator("[name=operation]").select_option("notify")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Record review action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(refresh_verification, True).result(timeout=30)
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/rectification/")
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill(
                "Read current received source before executing correction"
            )
            page.get_by_role("button", name="Record correction action", exact=True).click()
            page.get_by_role("link", name="Review correction proposal", exact=True).click()
            page.locator("[name=purpose]").fill(
                "Read approved received changes before correction execution"
            )
            page.get_by_role("button", name="Record review action", exact=True).click()
            page.locator("[name=operation]").select_option("execute")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Record review action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            page.goto(live_server.url + path)
            assert "Synthetic reviewed correction" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert RightsRectificationReview.objects.get().outcome == "approved"
    person.refresh_from_db()
    assert person.alias != alias_before
    assert person.alias == "Synthetic reviewed correction"
    person.listing.refresh_from_db()
    assert person.listing.status != "published"
    assert RightsRectificationNotification.objects.count() == 1


def test_proposal_history_pages_do_not_reveal_proposed_text(request, settings, monkeypatch):
    from apps.safety.crypto import seal
    from apps.safety.models import RightsAction, RightsRectificationProposal

    case, user, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    proof = case.proofs.latest("created_at")
    for _ in range(51):
        # Historical metadata fixtures, not approved or executed correction decisions.
        action = RightsAction.objects.create(
            key=uuid.uuid4(),
            request=case,
            actor=user,
            expected_version=case.version,
            operation="rectify_plan",
            payload_digest="f" * 64,
            encrypted_reason=seal({"reason": "Synthetic history fixture"}),
        )
        RightsRectificationProposal.objects.create(
            action=action,
            proof=proof,
            person=person,
            source_digest="e" * 64,
            encrypted_changes=seal({"alias": "Private historical correction"}),
        )
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    first = staff.get(path)
    second = staff.get(path, {"proposals_page": 2})
    assert first.status_code == second.status_code == 200
    assert len(first.context["proposals"]) == 50 and len(second.context["proposals"]) == 1
    assert first.context["proposals"].has_next() and second.context["proposals"].has_previous()
    assert set(item.pk for item in first.context["proposals"]).isdisjoint(
        item.pk for item in second.context["proposals"]
    )
    assert b"Private historical correction" not in first.content + second.content
    assert "encrypted_changes" in first.context["proposals"][0].get_deferred_fields()


@pytest.mark.parametrize("outcome", ["approved", "rejected"])
def test_reviewed_correction_communication_requires_new_proof_and_is_idempotent(
    request, settings, monkeypatch, outcome
):
    from django.core.exceptions import ValidationError

    from apps.safety.rectification_execution import notify
    from apps.safety.rectification_review import inspect, review

    case, reviewer, other, person, proposal, path, client, receipt = independent_case(
        request,
        settings,
        monkeypatch,
        with_receipt=True,
        changes={
            "alias": "Synthetic reviewed correction",
            "title": "Corrected synthetic title",
            "description": "Corrected synthetic description",
        },
    )
    reviewer.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    reviewer = User.objects.get(pk=reviewer.pk)
    preview(reviewer, case.pk, case.version, "Read current source before independent review")
    inspect(reviewer, case.pk, proposal.pk, case.version, "Read proposed changes independently")
    review(reviewer, case.pk, proposal.pk, uuid.uuid4(), case.version, outcome, REASON)
    case.refresh_from_db()
    key = uuid.uuid4()
    with pytest.raises(ValidationError):
        notify(reviewer, case.pk, proposal.pk, key, case.version, REASON)
    original = proposal.action.actor
    staff = Client()
    staff.force_login(original)
    session = staff.session
    session["mfa_version"] = original.mfa_version
    session.save()
    fresh(case, reviewer, other, original, staff)
    preview(reviewer, case.pk, case.version, "Read unchanged current source before communication")
    inspect(
        reviewer,
        case.pk,
        proposal.pk,
        case.version,
        "Read approved correction before communication",
    )
    version = case.version
    before = person.alias, person.listing.status, person.listing.lifecycle_version
    data = {"key": key, "version": version, "operation": "notify", "reason": REASON}
    if outcome == "rejected":
        assert other.post(path, data).status_code == 409
        assert not RightsRectificationNotification.objects.exists()
        return
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    assert other.post(path, {**data, "version": version - 1}).status_code == 409
    # Writer changes source without touching case.version: source HMAC must catch it.
    old_alias = person.alias
    type(person).objects.filter(pk=person.pk).update(alias="Changed synthetic current source")
    responses_before = case.responses.count()
    assert other.post(path, data).status_code == 409
    assert not RightsRectificationNotification.objects.exists()
    assert case.responses.count() == responses_before
    type(person).objects.filter(pk=person.pk).update(alias=old_alias)
    assert other.post(path, data).status_code == 302
    result = RightsRectificationNotification.objects.get()
    assert other.post(path, data).status_code == 302
    assert RightsRectificationNotification.objects.count() == 1
    assert other.post(path, {**data, "reason": REASON + " changed"}).status_code == 409
    reviewer.user_permissions.remove(Permission.objects.get(codename="respond_rights_request"))
    assert other.post(path, data).status_code == 403
    received = client.get(receipt)
    assert received.status_code == 200
    assert b"No changes have been applied yet" in received.content
    assert REASON.encode() not in received.content
    assert b"Synthetic reviewed correction" not in received.content
    acknowledgement = receipt + f"response/{result.response_id}/acknowledge/"
    assert (
        Client(enforce_csrf_checks=True).post(acknowledgement, {"received": "yes"}).status_code
        == 403
    )
    assert client.post(acknowledgement, {"received": "yes"}).status_code == 302
    assert client.post(acknowledgement, {"received": "yes"}).status_code == 302
    assert result.response.receipt_acknowledgement.channel_digest == case.receipt_digest
    assert result.response.kind == "progress"
    assert result.review.outcome == "approved"
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert (person.alias, person.listing.status, person.listing.lifecycle_version) == before

    from apps.safety.crypto import unseal
    from apps.safety.rectification_execution import execute

    case.refresh_from_db()
    execution_key = uuid.uuid4()
    with pytest.raises(ValidationError):
        execute(reviewer, case.pk, proposal.pk, execution_key, case.version, REASON)
    reviewer = User.objects.get(pk=reviewer.pk)
    fresh(case, reviewer, other, original, staff)
    preview(reviewer, case.pk, case.version, "Read received correction source before execution")
    inspect(
        reviewer,
        case.pk,
        proposal.pk,
        case.version,
        "Read received approved changes before execution",
    )
    old_revision = person.listing.approved_revision
    assert old_revision is not None
    old_title = old_revision.title
    old_description = old_revision.description
    old_rates = list(
        old_revision.rates.values_list("concept", "mode", "amount", "currency", "duration_minutes")
    )
    old_photos = list(
        old_revision.photos.filter(removed_at__isnull=True).values_list("blob_id", "position")
    )
    old_relations = {
        field.name: set(getattr(old_revision, field.name).values_list("pk", flat=True))
        for field in old_revision._meta.many_to_many
    }
    old_rights_version = person.rights_version
    execution_version = case.version
    payload = {
        "key": execution_key,
        "version": execution_version,
        "operation": "execute",
        "reason": REASON,
    }
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    from apps.listings.models import Revision
    from apps.mediafiles.tasks import process_blob

    assert old_rates and old_photos and all(old_relations.values())
    rate = old_revision.rates.first()
    original_concept = rate.concept
    rate.concept = "Changed synthetic source rate"
    rate.save(update_fields=["concept"])
    assert other.post(path, payload).status_code == 409
    rate.concept = original_concept
    rate.save(update_fields=["concept"])
    ongoing = Revision.objects.create(
        listing=person.listing, manager_version=person.manager_version
    )
    assert other.post(path, payload).status_code == 409
    ongoing.delete()  # Test-only competing draft, no user content.
    dispatched = []
    original_delay = process_blob.delay

    def record_dispatch(blob_id):
        dispatched.append(blob_id)
        return original_delay(blob_id)

    monkeypatch.setattr(process_blob, "delay", record_dispatch)
    assert other.post(path, payload).status_code == 302
    assert set(dispatched) == {str(blob_id) for blob_id, _ in old_photos}
    from apps.safety.models import RightsRectificationExecution

    applied = RightsRectificationExecution.objects.get()
    assert (
        execute(reviewer, case.pk, proposal.pk, execution_key, execution_version, REASON).pk
        == applied.pk
    )
    person.refresh_from_db()
    person.listing.refresh_from_db()
    assert person.alias == "Synthetic reviewed correction"
    assert person.rights_version == old_rights_version + 1
    assert person.listing.status != "published"
    assert person.listing.available_until is None
    assert unseal(applied.encrypted_previous_values)["alias"] == before[0]
    if old_revision:
        old_revision.refresh_from_db()
        assert old_revision.title == old_title
        assert old_revision.description == old_description
        corrected = applied.corrected_revision
        assert corrected.title == "Corrected synthetic title"
        assert corrected.description == "Corrected synthetic description"
        assert (
            list(
                corrected.rates.values_list(
                    "concept", "mode", "amount", "currency", "duration_minutes"
                )
            )
            == old_rates
        )
        assert set(corrected.photos.values_list("blob_id", "position")) == set(old_photos)
        assert not corrected.photos.filter(approved=True).exists()
        # Local eager processing may already have completed comparisons; dispatch is asserted above.
        for field, ids in old_relations.items():
            assert set(getattr(corrected, field).values_list("pk", flat=True)) == ids
        assert person.listing.approved_revision_id == old_revision.pk
        assert applied.corrected_revision.source_revision_id == old_revision.pk
        assert applied.corrected_revision.status == "draft"
        assert not applied.corrected_revision.publisher_acceptance_id
        assert not applied.corrected_revision.contact_exposure_accepted
