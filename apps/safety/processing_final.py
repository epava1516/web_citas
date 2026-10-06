"""Current effects consumed by the integrated restriction/objection response flow."""

from functools import partial

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from . import rights_final_response as final_response
from .erasure_inventory import canonical
from .models import ProcessingExecution, PurposeRestriction
from .processing_review import contents
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_verification import PROCEDURE, enabled


@sensitive_variables()
def snapshot(case, person, listing, execution_id):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Final processing material requires canonical scope locks")
    execution = (
        ProcessingExecution.objects.select_for_update(of=("self",))
        .select_related("action", "proof", "review__action", "review__plan__action")
        .filter(
            pk=execution_id,
            action__request=case,
            person=person,
            account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if not execution or case.kind not in {"restriction", "object"}:
        raise ValidationError("Executed own-scope processing decision required")
    review, proof = execution.review, execution.proof
    plan = review.plan
    if (
        not enabled()
        or proof.request_id != case.pk
        or proof.scope != case.kind
        or proof.status != "passed"
        or proof.provider != "simulator"
        or proof.procedure != PROCEDURE
        or proof.channel_digest != case.receipt_digest
        or proof.person_id != (person.pk if person else None)
        or proof.account_subject_id != case.account_subject_id
        or proof.expires_at <= timezone.now()
        or case.receipt_expires_at <= timezone.now()
        or proof.case_version != execution.action.expected_version
        or plan.action.request_id != case.pk
        or review.action.request_id != case.pk
        or plan.person_id != execution.person_id
        or plan.account_subject_id != execution.account_subject_id
        or review.outcome != "approved"
        or review.action.actor_id == plan.action.actor_id
        or review.proof_id != proof.pk
        or plan.proof_id != proof.pk
        or review.plan_digest != fingerprint(plan.encrypted_plan)
        or review.source_digest != plan.source_digest
        or execution.source_digest != plan.source_digest
    ):
        raise ValidationError("Original scoped processing approval unavailable or changed")
    raw_plan = checked_body(plan.encrypted_plan)
    body = contents(plan, raw_plan["manifest"])
    result = checked_body(execution.encrypted_result)
    reviewed_reason = checked_body(review.action.encrypted_reason)["reason"]
    if review.action.payload_digest != fingerprint(
        canonical(
            {
                "plan": str(plan.pk),
                "version": review.action.expected_version,
                "operation": "review",
                "reason": reviewed_reason,
                "outcome": "approved",
                "plan_digest": review.plan_digest,
            }
        )
    ):
        raise ValidationError("Processing approval integrity changed")
    decisions = {row["purpose"]: row for row in body["decisions"]}
    selected = result.get("blocked")
    if (
        result.get("schema") != "processing-execution-v1"
        or result.get("data_deleted") is not False
        or not isinstance(selected, list)
        or not selected
        or len(set(selected)) != len(selected)
        or not set(selected) <= {"account_preferences", "publication"}
        or result.get("remaining_purposes") != sorted(set(decisions) - set(selected))
        or any(
            p not in decisions or decisions[p]["operation"] not in {"restrict", "cease"}
            for p in selected
        )
    ):
        raise ValidationError("Processing execution result changed")
    reason = checked_body(execution.action.encrypted_reason)["reason"]
    if execution.action.payload_digest != fingerprint(
        canonical(
            {
                "plan": str(plan.pk),
                "version": execution.action.expected_version,
                "purposes": sorted(selected),
                "reason": reason,
                "confirmed": True,
            }
        )
    ):
        raise ValidationError("Processing execution action changed")
    outcomes = []
    for purpose, decision in sorted(decisions.items()):
        state = "pending"
        effect = None
        if decision["operation"] == "continue":
            state = "continued_with_reviewed_grounds"
        elif purpose in selected and purpose == "account_preferences":
            restriction = (
                PurposeRestriction.objects.select_for_update()
                .filter(
                    execution=execution,
                    purpose=purpose,
                    subject_id=case.account_subject_id or (person.subject_id if person else None),
                )
                .first()
            )
            if (
                restriction
                and restriction.active
                and restriction.mode == decision["operation"]
                and restriction.initial_review_on
                and restriction.initial_review_on.isoformat() == decision["review_on"]
            ):
                state = "restricted" if restriction.mode == "restrict" else "ceased"
                effect = {
                    "type": "preferences",
                    "id": restriction.pk,
                    "version": restriction.version,
                    "review_on": restriction.review_on.isoformat(),
                }
        elif purpose in selected and purpose == "publication":
            hold = execution.publication_hold
            if (
                hold
                and hold.active
                and person
                and hold.person_id == person.pk
                and hold.proof_id == proof.pk
                and hold.action_id == execution.action_id
                and hold.subject_snapshot == str(person.subject_id or "")
                and hold.manager_version == person.manager_version
                and hold.ground == "purpose_" + decision["operation"]
                and hold.initial_purpose_review_on
                and hold.initial_purpose_review_on.isoformat() == decision["review_on"]
                and listing
                and listing.status != "published"
                and not listing.available_until
            ):
                state = "restricted" if decision["operation"] == "restrict" else "ceased"
                effect = {
                    "type": "publication",
                    "id": hold.pk,
                    "version": hold.version,
                    "review_on": hold.purpose_review_on.isoformat()
                    if hold.purpose_review_on
                    else None,
                }
        outcomes.append(
            {
                **decision,
                "state": state,
                "effect": effect,
                "initial_review_on": decision["review_on"],
                "review_on": effect["review_on"] if effect else decision["review_on"],
            }
        )
    return {
        "schema": "processing-final-material-v1",
        "kind": case.kind,
        "execution": execution.pk,
        "proof": str(proof.pk),
        "plan_digest": fingerprint(plan.encrypted_plan),
        "review_digest": review.action.payload_digest,
        "execution_digest": fingerprint(execution.encrypted_result),
        "decisions": outcomes,
        "pending_purposes": sorted(row["purpose"] for row in outcomes if row["state"] == "pending"),
        "operational_pending": body["manifest"].get("pending", []),
        "data_deleted": False,
        "identity_simulated": True,
    }


def _projection(material, text):
    pending = bool(material["pending_purposes"] or material["operational_pending"])
    return pending, {
        "text": text,
        "simulation": True,
        "processing": {
            "kind": material["kind"],
            "complete": not pending,
            "data_deleted": False,
            "decisions": [
                {field: row.get(field) for field in ["purpose", "operation", "state", "review_on"]}
                for row in material["decisions"]
            ],
            "pending_purposes": material["pending_purposes"],
            "operational_pending": material["operational_pending"],
        },
    }


_POLICY = final_response.Policy(
    kinds=("restriction", "object"),
    prefix="process",
    schema="processing-final-draft-v1",
    execution_model=ProcessingExecution,
    snapshot=snapshot,
    projection=_projection,
    review_permission="safety.review_processing_plan",
)
_actor = partial(final_response._actor, _POLICY)
prepare = partial(final_response.prepare, _POLICY)
inspect = partial(final_response.inspect, _POLICY)
review = partial(final_response.review, _POLICY)
issue = partial(final_response.issue, _POLICY)
