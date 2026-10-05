"""Approved publication measures preserve data and use the canonical exposure guard."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_processing_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready
from test_rights_verification import read

from apps.core.models import User
from apps.listings.models import Favorite, Listing
from apps.listings.moderation import publicly_visible
from apps.safety.erasure_inventory import source_manifest
from apps.safety.models import PrivacyPublicationHold, ProcessingExecution, PurposeRestriction
from apps.safety.processing_execution import execute
from apps.safety.processing_plans import prepare
from apps.safety.processing_review import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("mode", ["restrict", "cease"])
@pytest.mark.parametrize("mixed", [False, True])
def test_reviewed_publication_pause_replay_preserves_data_and_central_guard(
    request, settings, monkeypatch, mode, mixed
):
    case, actor, original_staff, public, receipt, person = ready(
        request, settings, monkeypatch, "restriction"
    )
    listing = person.listing
    favorite = Favorite.objects.create(user=person.subject, listing=listing) if mixed else None
    selected = ["publication", "account_preferences"] if mixed else ["publication"]
    original = (listing.approved_revision_id, person.manager_version, listing.lifecycle_version)
    others = list(Listing.objects.exclude(pk=listing.pk).values_list("pk", "status"))
    with transaction.atomic():
        manifest = source_manifest(person, case)
    assert "publication" in {row["purpose"] for row in manifest["entries"]}
    values = [
        dict(
            purpose=p,
            operation=mode if p in selected else "continue",
            basis=REASON,
            reason=REASON,
            scope=REASON,
            review_on=(timezone.localdate() + timedelta(days=7)).isoformat(),
        )
        for p in sorted({row["purpose"] for row in manifest["entries"]})
    ]
    plan = prepare(actor, case.pk, uuid4(), case.version, REASON, values)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_processing_plan",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
    key = uuid4()
    version = case.version
    actor_client = Client()
    actor_client.force_login(actor)
    actor_session = actor_client.session
    actor_session["mfa_version"] = actor.mfa_version
    actor_session.save()
    execution_path = reverse("processing_execute", kwargs={"case_id": case.pk, "plan_id": plan.pk})
    page = actor_client.get(execution_path)
    assert page.status_code == 200
    assert "publication" in dict(page.context["form"].fields["purposes"].choices)
    values = dict(key=key, version=version, purposes=selected, reason=REASON, confirmed=True)
    response = actor_client.post(execution_path, values)
    assert response.status_code == 200
    assert b"Restricci" in response.content or b"Selected restriction applied" in response.content
    assert actor_client.post(execution_path, values).status_code == 200
    result = ProcessingExecution.objects.get(action__key=key)
    assert execute(actor, case.pk, plan.pk, key, version, selected, REASON, True).pk == result.pk
    assert ProcessingExecution.objects.count() == PrivacyPublicationHold.objects.count() == 1
    assert result.publication_hold.ground == "purpose_" + mode
    expected_date = timezone.localdate() + timedelta(days=7)
    assert result.publication_hold.purpose_review_on == expected_date
    assert result.publication_hold.initial_purpose_review_on == expected_date
    assert result.publication_hold.version == 1
    assert PurposeRestriction.objects.count() == int(mixed)
    if mixed:
        restriction = PurposeRestriction.objects.get()
        assert restriction.execution_id == result.pk and restriction.mode == mode
        assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert result.publication_hold.person_id == person.pk and result.publication_hold.active
    listing.refresh_from_db()
    person.refresh_from_db()
    assert (listing.approved_revision_id, person.manager_version, listing.lifecycle_version) == (
        original[0],
        original[1],
        original[2] + 1,
    )
    assert listing.status == "paused" and listing.available_until is None
    assert list(Listing.objects.exclude(pk=listing.pk).values_list("pk", "status")) == others
    Listing.objects.filter(pk=listing.pk).update(status="published")
    listing.refresh_from_db()
    assert not publicly_visible(listing)
    from apps.safety.privacy_release import actor_check

    with pytest.raises(ValidationError, match="Purpose measure"):
        reviewer.user_permissions.add(
            Permission.objects.get(codename="review_privacy_hold"),
            Permission.objects.get(codename="respond_rights_request"),
        )
        reviewer = User.objects.get(pk=reviewer.pk)
        actor_check(reviewer, case, result.publication_hold)

    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    response = client.get(reverse("privacy_hold_release", kwargs={"case_id": case.pk}))
    assert response.status_code == 409
    assert "no-store" in response["Cache-Control"]
    assert result.publication_hold.active

    from test_privacy_release import fresh

    from apps.safety.publication_purpose_release import inspect as inspect_release
    from apps.safety.rights_actions import act

    actor.user_permissions.add(
        Permission.objects.get(codename="manage_rights_assignment"),
        Permission.objects.get(codename="verify_rights_scope"),
    )
    actor = User.objects.get(pk=actor.pk)
    reviewer.user_permissions.add(Permission.objects.get(codename="release_purpose_restriction"))
    reviewer = User.objects.get(pk=reviewer.pk)
    case.refresh_from_db()
    act(actor, case.pk, uuid4(), case.version, "unassign", REASON)
    case.refresh_from_db()
    act(reviewer, case.pk, uuid4(), case.version, "claim", REASON)
    fresh(case, reviewer, client, actor, original_staff)
    inspection_key = uuid4()
    action, selected_decision = inspect_release(
        reviewer,
        case.pk,
        result.publication_hold_id,
        inspection_key,
        case.version,
        REASON,
    )
    assert selected_decision["operation"] == mode
    assert action.operation == "publication_rel_read"
    repeated, _ = inspect_release(
        reviewer,
        case.pk,
        result.publication_hold_id,
        inspection_key,
        case.version,
        REASON,
    )
    assert repeated.pk == action.pk
    release_path = reverse(
        "publication_purpose_release",
        kwargs={
            "case_id": case.pk,
            "hold_id": result.publication_hold_id,
        },
    )
    page = client.get(release_path)
    assert page.status_code == 200 and REASON.encode() not in page.content
    assert "no-store" in page["Cache-Control"]
    page = client.post(
        release_path,
        {
            "key": uuid4(),
            "version": case.version,
            "operation": "inspect",
            "reason": REASON,
        },
    )
    assert page.status_code == 200 and page.context["decision"]["operation"] == mode
    assert REASON.encode() not in client.get(release_path).content
    result.publication_hold.refresh_from_db()
    assert result.publication_hold.active
    from apps.safety.models import PrivacyHoldReleaseProposal, RightsAction
    from apps.safety.publication_purpose_release import propose as propose_release

    if mode == "restrict":
        from apps.safety.models import ProcessingPlanReview

        review = result.review
        approval_signature = review.action.payload_digest
        RightsAction.objects.filter(pk=review.action_id).update(payload_digest="0" * 64)
        with pytest.raises(ValidationError, match="approval record changed"):
            inspect_release(
                reviewer, case.pk, result.publication_hold_id, uuid4(), case.version, REASON
            )
        RightsAction.objects.filter(pk=review.action_id).update(payload_digest=approval_signature)
        original_signature = action.payload_digest
        RightsAction.objects.filter(pk=action.pk).update(payload_digest="0" * 64)
        with pytest.raises(ValidationError, match="inspection changed"):
            propose_release(
                reviewer,
                case.pk,
                result.publication_hold_id,
                uuid4(),
                case.version,
                action.pk,
                REASON,
                "restriction_resolved",
            )
        RightsAction.objects.filter(pk=action.pk).update(payload_digest=original_signature)
        ProcessingPlanReview.objects.filter(pk=review.pk).update(outcome="rejected")
        with pytest.raises(ValidationError):
            inspect_release(
                reviewer, case.pk, result.publication_hold_id, uuid4(), case.version, REASON
            )
        ProcessingPlanReview.objects.filter(pk=review.pk).update(outcome="approved")
        original_cipher = action.encrypted_reason
        RightsAction.objects.filter(pk=action.pk).update(encrypted_reason="damaged-audit-cipher")
        previous_proposals = PrivacyHoldReleaseProposal.objects.count()
        with pytest.raises(ValidationError, match="inspection record unavailable"):
            propose_release(
                reviewer,
                case.pk,
                result.publication_hold_id,
                uuid4(),
                case.version,
                action.pk,
                REASON,
                "restriction_resolved",
            )
        assert PrivacyHoldReleaseProposal.objects.count() == previous_proposals
        result.publication_hold.refresh_from_db()
        assert result.publication_hold.active
        RightsAction.objects.filter(pk=action.pk).update(encrypted_reason=original_cipher)

    def propose_ui(
        user, case_id, hold_id, key, version, read_id, reason, ground, resume_message_id=None
    ):
        values = dict(
            key=key,
            version=version,
            operation="propose",
            read_id=read_id,
            reason=reason,
            ground=ground,
        )
        if resume_message_id:
            values["resume_message_id"] = resume_message_id
        response = client.post(release_path, values)
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert (
            b"Proposal recorded" in response.content or b"Propuesta registrada" in response.content
        )
        return PrivacyHoldReleaseProposal.objects.get(action__key=key)

    incomplete = client.post(
        release_path, dict(key=uuid4(), version=case.version, operation="propose", reason=REASON)
    )
    assert incomplete.status_code == 400
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(reviewer)
    csrf_session = csrf_client.session
    csrf_session["mfa_version"] = reviewer.mfa_version
    csrf_session.save()
    assert (
        csrf_client.post(
            release_path,
            dict(key=uuid4(), version=case.version, operation="inspect", reason=REASON),
        ).status_code
        == 403
    )
    proposal_key = uuid4()
    if mode == "cease":
        with pytest.raises(ValidationError, match="new subject request"):
            propose_release(
                reviewer,
                case.pk,
                result.publication_hold_id,
                proposal_key,
                case.version,
                action.pk,
                REASON,
                "resume_requested",
            )
    else:
        proposal = propose_ui(
            reviewer,
            case.pk,
            result.publication_hold_id,
            proposal_key,
            case.version,
            action.pk,
            REASON,
            "restriction_resolved",
        )
        assert proposal.purpose_read_id == action.pk and proposal.released_at is None
        assert proposal.response.kind == "progress"
        with transaction.atomic():
            original_inventory = source_manifest(person, case)
        from apps.safety.models import PrivacyHoldReleaseProposal

        PrivacyHoldReleaseProposal.objects.filter(pk=proposal.pk).update(ground="resume_requested")
        with transaction.atomic():
            changed_inventory = source_manifest(person, case)
        assert changed_inventory != original_inventory
        assert REASON not in str(changed_inventory)
        PrivacyHoldReleaseProposal.objects.filter(pk=proposal.pk).update(
            ground="restriction_resolved"
        )
        assert (
            propose_release(
                reviewer,
                case.pk,
                result.publication_hold_id,
                proposal_key,
                proposal.action.expected_version,
                action.pk,
                REASON,
                "restriction_resolved",
            ).pk
            == proposal.pk
        )
    if mode == "cease":
        from apps.safety.models import RightsMessage

        message_key = uuid4()
        case.refresh_from_db()
        assert (
            public.post(
                receipt,
                {
                    "key": message_key,
                    "version": case.version,
                    "text": "Solicito reanudar la publicación de mi perfil tras revisión.",
                },
            ).status_code
            == 302
        )
        message = RightsMessage.objects.get(key=message_key)
        fresh(case, reviewer, client, actor, original_staff)
        action, _ = inspect_release(
            reviewer, case.pk, result.publication_hold_id, uuid4(), case.version, REASON
        )
        proposal = propose_ui(
            reviewer,
            case.pk,
            result.publication_hold_id,
            uuid4(),
            case.version,
            action.pk,
            REASON,
            "resume_requested",
            message.pk,
        )
        assert proposal.resume_message_id == message.pk
    result.publication_hold.refresh_from_db()
    assert result.publication_hold.active

    if mode in {"restrict", "cease"}:
        from test_privacy_release import confirm

        from apps.safety.publication_purpose_release import execute as release

        case.refresh_from_db()
        with pytest.raises(ValidationError):
            release(
                reviewer,
                case.pk,
                result.publication_hold_id,
                proposal.pk,
                uuid4(),
                case.version,
                REASON,
            )
        confirm(public, receipt, proposal)
        new_proof = fresh(case, reviewer, client, actor, original_staff)
        release_key = uuid4()
        release_version = case.version
        release_values = dict(
            key=release_key,
            version=release_version,
            operation="execute",
            proposal_id=proposal.pk,
            reason=REASON,
        )
        response = client.post(release_path, release_values)
        assert response.status_code == 200
        # Template signals may also capture nested browser/widget renders.
        assert (
            b"Release recorded" in response.content
            or b"Levantamiento registrado" in response.content
        )
        released = PrivacyHoldReleaseProposal.objects.get(pk=proposal.pk)
        assert released.released_at is not None
        assert client.post(release_path, release_values).status_code == 200
        assert released.released_proof_id == new_proof.pk
        assert (
            release(
                reviewer,
                case.pk,
                result.publication_hold_id,
                proposal.pk,
                release_key,
                release_version,
                REASON,
            ).pk
            == released.pk
        )
        result.publication_hold.refresh_from_db()
        listing.refresh_from_db()
        case.refresh_from_db()
        assert not result.publication_hold.active and listing.status == "paused"
        assert case.status == "reviewing" and case.scope_status == "unverified"
        if mixed:
            assert PurposeRestriction.objects.get().active
