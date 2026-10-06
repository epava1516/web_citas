"""Recipient assessment/review for executed rights, using the existing action ledger.

History identifies candidates, never proven disclosure. External recipients,
contact authority and actual delivery remain explicit pending work.
"""

from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .models import ErasureExecution, ProcessingExecution, RightsAccess, RightsAction
from .recipient_assessments import validate_decisions
from .recipient_candidates import manager_evidence
from .rights_access_response_draft import checked_body
from .rights_copy_page_review import fresh_authority
from .rights_final_response import _context, _digest, _record


def backend(case_id):
    from . import erasure_final, processing_final
    from .models import RightsRequest

    kind = RightsRequest.objects.get(pk=case_id).kind
    if kind == "erase":
        return erasure_final
    if kind in {"restriction", "object"}:
        return processing_final
    raise ValidationError("Executed erasure, restriction or objection required")


@sensitive_variables()
def snapshot(case, person, listing, execution_id):
    current_backend = backend(case.pk)
    effects = current_backend.snapshot(case, person, listing, execution_id)
    model = ErasureExecution if case.kind == "erase" else ProcessingExecution
    execution = model.objects.get(pk=execution_id, action__request=case)
    latest = model.objects.filter(action__request=case).order_by("-action_id").first()
    if not latest or latest.pk != execution.pk:
        raise ValidationError("Latest own-scope communication execution required")
    candidates = {}

    def add(kind, reference, basis, record):
        if kind not in {"individual", "agency", "account"} or not reference:
            return
        key = kind, str(reference)
        candidate = candidates.setdefault(
            key, {"kind": kind, "reference": str(reference), "evidence": []}
        )
        candidate["evidence"].append({"basis": basis, "record": str(record)})

    if person:
        for row in manager_evidence(person):
            add(*row)
        own_history = Q(request__person=person)
    else:
        # Agency ownership is never an authorization to include its models.
        own_history = Q(request__account_subject_id=case.account_subject_id)
    for access in (
        RightsAccess.objects.filter(own_history, created_at__lte=execution.created_at)
        .exclude(request=case)
        .order_by("pk")
    ):
        add("account", access.actor_id, "historical_rights_procedure_access", access.pk)
    return {
        "schema": "rights-communication-source-v1",
        "kind": case.kind,
        "execution": str(execution.pk),
        "effects_digest": _digest(effects),
        "person": str(person.pk) if person else None,
        "account_subject": str(case.account_subject_id) if case.account_subject_id else None,
        "cutoff": execution.created_at.isoformat(),
        "candidates": [candidates[key] for key in sorted(candidates)],
        "manager_notices": [],
        "complete": False,
        "pending": [
            "actual_disclosures_and_recipient_scope_review",
            "current_request_operator_handling",
            "public_audience_and_reuse_without_identified_recipients",
            "processors_and_external_destinations_register",
            "historical_recipient_contact_authorization_and_delivery",
        ],
    }


@transaction.atomic
@sensitive_variables()
def inspect_source(user, case_id, version, responses, execution_id, purpose):
    case, person, listing = _context(
        backend(case_id)._POLICY, user, case_id, version, responses, assigned=True
    )
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited recipient source access purpose required")
    access = _record(
        user,
        case,
        uuid4(),
        "comms_source_access",
        {
            "execution": str(execution_id),
            "responses": responses,
            "channel": case.receipt_digest,
            "purpose": purpose,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    source = snapshot(case, person, listing, execution_id)
    read = _record(
        user,
        case,
        uuid4(),
        "rights_comms_source",
        {
            "execution": str(execution_id),
            "digest": _digest(source),
            "access": access.pk,
            "responses": responses,
            "channel": case.receipt_digest,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    return read, source


def source_read(user, case, source, responses):
    read = (
        RightsAction.objects.filter(
            request=case,
            actor=user,
            expected_version=case.version,
            operation="rights_comms_source",
        )
        .order_by("-pk")
        .first()
    )
    if not read:
        raise ValidationError("Read the current recipient source before assessment")
    body = checked_body(read.encrypted_reason)
    if (
        _digest(body) != read.payload_digest
        or body.get("digest") != _digest(source)
        or body.get("execution") != source["execution"]
        or body.get("responses") != responses
        or body.get("channel") != case.receipt_digest
    ):
        raise ValidationError("Read the current recipient source before assessment")
    fresh_authority(user, case, body["session"], body["mfa"])
    return read


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, version, responses, execution_id, key, purpose, decisions):
    policy = backend(case_id)._POLICY
    case, person, listing = _context(policy, user, case_id, version, responses, assigned=True)
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited assessment purpose required")
    source = snapshot(case, person, listing, execution_id)
    validate_decisions(source, decisions)
    inspected_source = source_read(user, case, source, responses)
    return _record(
        user,
        case,
        key,
        "rights_comms_plan",
        {
            "schema": "rights-communication-plan-v1",
            "version": version,
            "responses": responses,
            "channel": case.receipt_digest,
            "source": source,
            "source_read": inspected_source.pk,
            "decisions": decisions,
            "purpose": purpose,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )


@sensitive_variables()
def current(user, case_id, version, responses, plan_id):
    policy = backend(case_id)._POLICY
    case, person, listing = _context(policy, user, case_id, version, responses, assigned=False)
    if not User.objects.get(pk=user.pk).has_perm("safety.review_recipient_assessment"):
        raise PermissionDenied
    plan = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(pk=plan_id, request=case, operation="rights_comms_plan", expected_version=version)
        .first()
    )
    if not plan:
        raise ValidationError("Own-scope communication assessment required")
    if plan.actor_id == user.pk:
        raise PermissionDenied("Independent recipient reviewer required")
    body = checked_body(plan.encrypted_reason)
    policy_actor = backend(case_id)._actor
    policy_actor(plan.actor, case, assigned=True)
    fresh_authority(plan.actor, case, body["session"], body["mfa"])
    latest = (
        RightsAction.objects.filter(
            request=case, operation="rights_comms_plan", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if (
        _digest(body) != plan.payload_digest
        or latest.pk != plan.pk
        or body.get("schema") != "rights-communication-plan-v1"
        or body.get("version") != version
        or body["responses"] != responses
        or body["channel"] != case.receipt_digest
        or _digest(snapshot(case, person, listing, body["source"]["execution"]))
        != _digest(body["source"])
    ):
        raise ValidationError("Communication source or assessment changed")
    validate_decisions(body["source"], body["decisions"])
    return case, plan, body


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, version, responses, plan_id, purpose):
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited independent access purpose required")
    # Record access before decrypting any candidate or assessment grounds.
    case, _, _ = _context(
        backend(case_id)._POLICY, user, case_id, version, responses, assigned=False
    )
    if not User.objects.get(pk=user.pk).has_perm("safety.review_recipient_assessment"):
        raise PermissionDenied
    plan = RightsAction.objects.filter(
        pk=plan_id, request=case, operation="rights_comms_plan", expected_version=version
    ).first()
    if not plan:
        raise ValidationError("Own-scope communication assessment required")
    if plan.actor_id == user.pk:
        raise PermissionDenied("Independent recipient reviewer required")
    read = _record(
        user,
        case,
        uuid4(),
        "rights_comms_read",
        {
            "plan": plan.pk,
            "digest": plan.payload_digest,
            "purpose": purpose,
            "responses": responses,
            "channel": case.receipt_digest,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    _, _, body = current(user, case_id, version, responses, plan_id)
    return read, body


@transaction.atomic
@sensitive_variables()
def review(user, case_id, version, responses, plan_id, read_id, key, outcome, reason):
    case, plan, body = current(user, case_id, version, responses, plan_id)
    if (
        outcome not in {"approved", "rejected"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Motivated independent assessment review required")
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=user,
        expected_version=version,
        operation="rights_comms_read",
    ).first()
    if not read:
        raise ValidationError("Exact audited communication assessment read required")
    inspected = checked_body(read.encrypted_reason)
    if (
        _digest(inspected) != read.payload_digest
        or inspected["plan"] != plan.pk
        or inspected["digest"] != plan.payload_digest
        or inspected.get("responses") != responses
        or inspected.get("channel") != case.receipt_digest
    ):
        raise ValidationError("Communication read integrity changed")
    fresh_authority(user, case, inspected["session"], inspected["mfa"])
    return _record(
        user,
        case,
        key,
        "rights_comms_review",
        {
            "plan": plan.pk,
            "digest": plan.payload_digest,
            "read": read.pk,
            "outcome": outcome,
            "reason": reason,
            "pending": any(row["outcome"] == "pending" for row in body["decisions"].values()),
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
