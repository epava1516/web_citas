"""An independently notified proposal cannot deactivate a purpose restriction."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from test_processing_execution import prepared as prepared_execution
from test_processing_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import (
    PurposeReleaseProposal,
    PurposeRestriction,
    PurposeRestrictionRead,
    RightsResponse,
)
from apps.safety.processing_execution import execute
from apps.safety.purpose_release import inspect, propose
from apps.safety.rights_actions import act
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch, mode="restrict"):
    import test_processing_execution
    import test_processing_review

    prepare_plan = test_processing_execution.prepare

    def selected_mode(actor, case_id, key, version, reason, values):
        for item in values:
            if item["purpose"] == "account_preferences":
                item["operation"] = mode
        return prepare_plan(actor, case_id, key, version, reason, values)

    monkeypatch.setattr(test_processing_execution, "prepare", selected_mode)
    receipts = []
    original = test_processing_review.prepared_account

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        receipts.append(result[5])
        return result

    monkeypatch.setattr(test_processing_review, "prepared_account", capture)
    case, creator, subject, plan, favorite, client = prepared_execution(
        request, settings, monkeypatch
    )
    execute(creator, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True)
    case.refresh_from_db()
    creator.user_permissions.add(
        *Permission.objects.filter(codename__in=["manage_rights_assignment", "verify_rights_scope"])
    )
    creator = User.objects.get(pk=creator.pk)
    case = act(creator, case.pk, uuid4(), case.version, "unassign", REASON)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["release_purpose_restriction", "respond_rights_request"]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    case = act(reviewer, case.pk, uuid4(), case.version, "claim", REASON)
    read(client, case)
    proof = start(reviewer, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    from django.test import Client

    verifier = Client()
    verifier.force_login(creator)
    session = verifier.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    read(verifier, case)
    receive_event(creator, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(client, case)
    case._receipt_path = receipts[0]
    return case, creator, reviewer, client, subject, favorite, PurposeRestriction.objects.get()


def test_audited_http_proposal_notifies_without_releasing_or_leaking_private_reason(
    request, settings, monkeypatch
):
    case, creator, reviewer, client, subject, favorite, restriction = prepared(
        request, settings, monkeypatch
    )
    path = reverse(
        "purpose_restriction_release", kwargs={"case_id": case.pk, "restriction_id": restriction.pk}
    )
    assert client.get(path).status_code == 200 and REASON not in client.get(path).content.decode()
    payload = {
        "key": uuid4(),
        "version": case.version,
        "reason": REASON,
        "operation": "propose",
        "ground": "restriction_resolved",
    }
    assert client.post(path, payload).status_code == 409
    reading = {"key": uuid4(), "version": case.version, "reason": REASON, "operation": "inspect"}
    response = client.post(path, reading)
    assert response.status_code == 200 and response.context["body"]["enforced"] is False
    assert (
        client.post(path, reading).status_code == 200
        and PurposeRestrictionRead.objects.count() == 1
    )
    queue = reverse("purpose_restriction_queue", kwargs={"case_id": case.pk})
    listing = client.get(queue)
    assert listing.status_code == 200 and path in listing.content.decode()
    assert REASON not in listing.content.decode()
    assert listing["Cache-Control"] == "private, no-store"
    assert client.get(queue, {"state": "released"}).context["measures"].paginator.count == 0
    assert client.get(queue, {"purpose": "unknown"}).status_code == 400
    assert client.post(queue).status_code == 405
    before = (case.initial_due_at, subject.email, subject.session_version)
    result = client.post(path, payload)
    assert result.status_code == 200 and client.post(path, payload).status_code == 200
    proposal = PurposeReleaseProposal.objects.get()
    assert proposal.response.kind == "progress" and proposal.released_at is None
    assert RightsResponse.objects.count() == 1
    restriction.refresh_from_db()
    case.refresh_from_db()
    subject.refresh_from_db()
    assert restriction.active and case.status == "reviewing" and case.scope_status == "unverified"
    assert (case.initial_due_at, subject.email, subject.session_version) == before
    assert REASON not in client.get(path).content.decode()
    creator.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["release_purpose_restriction", "respond_rights_request"]
        )
    )
    creator = User.objects.get(pk=creator.pk)
    with pytest.raises(PermissionDenied):
        inspect(creator, case.pk, restriction.pk, uuid4(), case.version, REASON)


def test_cause_cannot_be_changed_to_resume_without_reviewed_new_request(
    request, settings, monkeypatch
):
    case, _, reviewer, _, _, _, restriction = prepared(request, settings, monkeypatch)
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    with pytest.raises(ValidationError):
        propose(
            reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON, "resume_requested"
        )
    assert not PurposeReleaseProposal.objects.exists() and restriction.active


@pytest.mark.parametrize("other_active", [False, True])
def test_received_proposal_needs_later_proof_then_releases_only_selected_measure(
    request, settings, monkeypatch, other_active
):
    from django.test import Client

    from apps.listings.models import Favorite
    from apps.safety.purpose_release import execute as release

    case, creator, reviewer, client, subject, favorite, restriction = prepared(
        request, settings, monkeypatch
    )
    other = None
    if other_active:
        # Synthetic pre-existing second measure tests isolation of release effects;
        # this fixture does not verify another preparation/review/execution workflow.
        from apps.safety.models import ProcessingExecution, RightsAction

        original = restriction.execution
        action = RightsAction.objects.create(
            key=uuid4(),
            request=case,
            actor=creator,
            expected_version=case.version,
            operation="processing_execute",
            payload_digest=original.action.payload_digest,
            encrypted_reason=original.action.encrypted_reason,
        )
        second = ProcessingExecution.objects.create(
            action=action,
            review=original.review,
            proof=original.proof,
            account_subject=subject,
            source_digest=original.source_digest,
            encrypted_result=original.encrypted_result,
        )
        other = PurposeRestriction.objects.create(
            execution=second,
            subject=subject,
            purpose=restriction.purpose,
            mode=restriction.mode,
            review_on=restriction.review_on,
        )
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    proposal = propose(
        reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON, "restriction_resolved"
    )
    case.refresh_from_db()
    read(client, case)
    with pytest.raises(ValidationError):
        release(reviewer, case.pk, restriction.pk, uuid4(), case.version, proposal.pk, REASON)
    public = Client()
    assert (
        public.post(
            case._receipt_path + f"response/{proposal.response_id}/acknowledge/",
            {"received": "yes"},
        ).status_code
        == 302
    )
    proof = start(reviewer, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    verifier = Client()
    verifier.force_login(creator)
    session = verifier.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    read(verifier, case)
    receive_event(creator, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(client, case)
    key = uuid4()
    version = case.version
    result = release(reviewer, case.pk, restriction.pk, key, version, proposal.pk, REASON)
    assert (
        release(reviewer, case.pk, restriction.pk, key, version, proposal.pk, REASON).pk
        == result.pk
    )
    restriction.refresh_from_db()
    case.refresh_from_db()
    assert not restriction.active and result.released_at and result.released_proof_id == proof.pk
    assert case.status == "reviewing" and case.scope_status == "unverified"
    own = Client()
    own.force_login(subject)
    assert (
        own.get(reverse("favorites")).status_code == (409 if other_active else 200)
        and Favorite.objects.filter(pk=favorite.pk).exists()
    )
    if other:
        other.refresh_from_db()
        assert other.active and not other.release_proposals.exists()


@pytest.mark.parametrize("corruption", ["cipher", "reason", "ground"])
def test_changed_proposal_is_rejected_without_releasing(request, settings, monkeypatch, corruption):
    from apps.safety.crypto import seal
    from apps.safety.models import RightsAction
    from apps.safety.purpose_release import execute as release

    case, _, reviewer, _, _, favorite, restriction = prepared(request, settings, monkeypatch)
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    proposal = propose(
        reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON, "restriction_resolved"
    )
    case.refresh_from_db()
    before = (case.version, case.scope_status, RightsAction.objects.count())
    if corruption == "ground":
        PurposeReleaseProposal.objects.filter(pk=proposal.pk).update(ground="resume_requested")
    else:
        payload = (
            "invalid-ciphertext" if corruption == "cipher" else seal({"other": "missing reason"})
        )
        RightsAction.objects.filter(pk=proposal.action_id).update(encrypted_reason=payload)
    with pytest.raises(ValidationError, match="Proposal record"):
        release(reviewer, case.pk, restriction.pk, uuid4(), case.version, proposal.pk, REASON)
    restriction.refresh_from_db()
    proposal.refresh_from_db()
    case.refresh_from_db()
    assert restriction.active and proposal.released_at is None
    assert (case.version, case.scope_status, RightsAction.objects.count()) == before
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()


def test_executed_cease_requires_a_new_subject_request(request, settings, monkeypatch):
    case, _, reviewer, _, _, favorite, restriction = prepared(
        request, settings, monkeypatch, mode="cease"
    )
    assert restriction.mode == "cease" and restriction.active
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    for ground in ["restriction_resolved", "resume_requested"]:
        with pytest.raises(ValidationError, match="new subject request"):
            propose(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON, ground)
    restriction.refresh_from_db()
    assert restriction.active and not PurposeReleaseProposal.objects.exists()
    assert not RightsResponse.objects.exists()
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()


@pytest.mark.parametrize("sender", ["subject", "anonymous", "moderator"])
def test_cease_proposal_requires_reviewed_new_message_from_subject_channel(
    request, settings, monkeypatch, sender
):
    from django.test import Client

    from apps.safety.models import RightsMessage

    case, creator, reviewer, client, subject, _, restriction = prepared(
        request, settings, monkeypatch, mode="cease"
    )
    public = Client()
    if sender != "anonymous":
        public.force_login(subject if sender == "subject" else creator)
    key = uuid4()
    response = public.post(
        case._receipt_path,
        {
            "key": key,
            "version": case.version,
            "text": "Solicito reanudar mis preferencias de cuenta.",
        },
    )
    assert response.status_code == 302
    message = RightsMessage.objects.get(key=key)
    assert message.created_at > restriction.execution.created_at
    case.refresh_from_db()
    read(client, case)
    proof = start(reviewer, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    verifier = Client()
    verifier.force_login(creator)
    session = verifier.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    read(verifier, case)
    receive_event(creator, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(client, case)
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    args = (
        reviewer,
        case.pk,
        restriction.pk,
        uuid4(),
        case.version,
        REASON,
        "resume_requested",
        message.pk,
    )
    if sender == "moderator":
        with pytest.raises(ValidationError, match="new subject request"):
            propose(*args)
        assert not PurposeReleaseProposal.objects.exists() and not RightsResponse.objects.exists()
    else:
        proposal = propose(*args)
        assert proposal.resume_message_id == message.pk and proposal.ground == "resume_requested"
        assert proposal.released_at is None and proposal.response.kind == "progress"
    restriction.refresh_from_db()
    assert restriction.active


def test_restriction_mode_must_match_signed_original_decision(request, settings, monkeypatch):
    case, _, reviewer, _, _, _, restriction = prepared(request, settings, monkeypatch)
    PurposeRestriction.objects.filter(pk=restriction.pk).update(mode="cease")
    with pytest.raises(ValidationError, match="Original plan unavailable"):
        inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    assert not PurposeRestrictionRead.objects.exists()
    assert not PurposeReleaseProposal.objects.exists()
    assert PurposeRestriction.objects.get(pk=restriction.pk).active
