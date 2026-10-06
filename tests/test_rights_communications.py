"""Actual execution-bound recipient review; synthetic identities, PostgreSQL."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import Client
from test_erasure_execution import PURPOSES, REASON, plan_fixture
from test_processing_execution import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read as read_case

from apps.core.models import User
from apps.safety import rights_communications as communications
from apps.safety.models import RightsAction
from apps.safety.recipient_assessments import targets
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("kind", ["erase", "restriction", "object"])
def test_review_is_independent_exact_audited_and_never_implies_delivery(
    request, settings, monkeypatch, kind
):
    if kind == "erase":
        from apps.safety.erasure_execution import execute

        case, actor, staff, _, _, _, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
        execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    else:
        import test_processing_review

        from apps.safety.processing_execution import execute

        original = test_processing_review.prepared_account
        monkeypatch.setattr(
            test_processing_review,
            "prepared_account",
            lambda request, settings, monkeypatch, _: original(
                request, settings, monkeypatch, kind
            ),
        )
        case, actor, _, plan, _, _ = prepared(request, settings, monkeypatch)
        execution = execute(
            actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True
        )
        staff = Client()
        staff.force_login(actor)
        session = staff.session
        session["mfa_version"] = actor.mfa_version
        session.save()
    case.refresh_from_db()
    read_case(staff, case)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.mfa_enabled = True
    reviewer.mfa_version = 1
    reviewer.save(update_fields=["mfa_enabled", "mfa_version"])
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "respond_rights_request",
                "review_recipient_assessment",
                "review_processing_plan",
            ]
        )
    )
    other = Client()
    other.force_login(reviewer)
    session = other.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read_case(other, case)
    with transaction.atomic():
        current, person, listing = locked_case(
            case.pk, lock_listing=True, allow_erased_account=True
        )
        source = communications.snapshot(current, person, listing, execution.pk)
    assert source["kind"] == kind and source["complete"] is False
    assert not source["manager_notices"] and source["pending"]
    decisions = {
        token: {"outcome": "pending", "reason": REASON, "evidence": REASON}
        for token in targets(source)
    }
    common = (case.pk, case.version, case.response_version)
    with pytest.raises(ValidationError, match="Assess every"):
        communications.propose(
            actor, *common, execution.pk, uuid4(), "Assess incomplete recipient scope", {}
        )
    false_delivery = {
        token: dict(value, outcome="communicated") for token, value in decisions.items()
    }
    with pytest.raises(ValidationError, match="Recorded recipient receipt"):
        communications.propose(
            actor,
            *common,
            execution.pk,
            uuid4(),
            "Assess unsupported recipient delivery",
            false_delivery,
        )
    with pytest.raises(ValidationError, match="Read the current recipient source"):
        communications.propose(
            actor,
            *common,
            execution.pk,
            uuid4(),
            "Assess source without prior audited access",
            decisions,
        )
    source_audit, inspected_source = communications.inspect_source(
        actor, *common, execution.pk, "Inspect current recipients before assessment"
    )
    assert inspected_source == source and source_audit.operation == "rights_comms_source"
    key = uuid4()
    proposal = communications.propose(
        actor, *common, execution.pk, key, "Assess recipients of the executed right", decisions
    )
    assert (
        communications.propose(
            actor, *common, execution.pk, key, "Assess recipients of the executed right", decisions
        ).pk
        == proposal.pk
    )
    with pytest.raises(PermissionDenied):
        communications.inspect(
            actor, *common, proposal.pk, "Attempt independent review of own plan"
        )
    with pytest.raises(ValidationError, match="Exact audited"):
        communications.review(reviewer, *common, proposal.pk, 0, uuid4(), "approved", REASON)
    # Decryption must happen after a transaction-visible audit was recorded.
    original_checked = communications.checked_body

    def checked_after_audit(cipher):
        if cipher == proposal.encrypted_reason:
            assert RightsAction.objects.filter(
                request=case, actor=reviewer, operation="rights_comms_read"
            ).exists()
        return original_checked(cipher)

    monkeypatch.setattr(communications, "checked_body", checked_after_audit)
    audit, body = communications.inspect(
        reviewer, *common, proposal.pk, "Read exact recipient grounds independently"
    )
    assert body["decisions"] == decisions
    review_key = uuid4()
    accepted = communications.review(
        reviewer, *common, proposal.pk, audit.pk, review_key, "approved", REASON
    )
    assert (
        communications.review(
            reviewer, *common, proposal.pk, audit.pk, review_key, "approved", REASON
        ).pk
        == accepted.pk
    )
    assert original_checked(accepted.encrypted_reason)["pending"] is True
    # Even a cached permission must not survive database revocation.
    assert reviewer.has_perm("safety.review_recipient_assessment")
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_recipient_assessment"))
    with pytest.raises(PermissionDenied):
        communications.inspect(
            reviewer, *common, proposal.pk, "Read after revoked review permission"
        )
    case.refresh_from_db()
    assert case.status == "reviewing" and case.version == common[1]
    reviewer.user_permissions.add(Permission.objects.get(codename="review_recipient_assessment"))
    path = f"/en/moderation/rights/{case.pk}/communications/"
    assert staff.get(path).status_code == 200
    assert b"Read exact recipient" not in staff.get(path).content
    assert Client(enforce_csrf_checks=True).post(path).status_code == 403
    metadata = {"version": case.version, "responses": case.response_version, "key": uuid4()}
    accessed = staff.post(
        path,
        metadata
        | {
            "operation": "source",
            "execution": execution.pk,
            "purpose": "Read recipients through private structured screen",
        },
    )
    assert accessed.status_code == 200 and accessed.context["decisions"]
    fields = {"decisions-TOTAL_FORMS": len(decisions), "decisions-INITIAL_FORMS": len(decisions)}
    for number, (token, value) in enumerate(decisions.items()):
        fields[f"decisions-{number}-target"] = token
        for field, content in value.items():
            fields[f"decisions-{number}-{field}"] = content
    posted = staff.post(
        path,
        metadata
        | fields
        | {
            "operation": "propose",
            "execution": execution.pk,
            "purpose": "Assess recipients through private structured screen",
        },
    )
    assert posted.status_code == 302
    latest = RightsAction.objects.filter(request=case, operation="rights_comms_plan").latest("pk")
    seen = other.post(
        path,
        metadata
        | {
            "operation": "inspect",
            "plan": latest.pk,
            "purpose": "Read proposed recipient decisions independently",
        },
    )
    assert seen.status_code == 200 and seen.context["inspected"]["decisions"] == decisions
    assert other.get(path).context["inspected"] is None
    recorded = other.post(
        path,
        metadata
        | {
            "operation": "review",
            "key": uuid4(),
            "plan": latest.pk,
            "read": seen.context["form"].initial["read"],
            "outcome": "approved",
            "reason": REASON,
        },
    )
    assert recorded.status_code == 302, recorded.context["form"].errors
