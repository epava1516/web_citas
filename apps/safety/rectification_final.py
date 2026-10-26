"""Integrated final correction response using the existing encrypted action ledger.

Preparation and independent review do not resolve a case. Explicit pending
recipient decisions prevent completion. No publication state is changed here.
"""

import json
import uuid
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsNotice,
    RightsRectificationExecution,
    RightsRectificationRecipientReview,
    RightsResponse,
)
from .recipient_assessments import validate_decisions
from .rectification_authority import capture_authority
from .rectification_recipients import execution_scope_matches, snapshot
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_copy_page_review import fresh_authority
from .rights_exports import canonical
from .rights_response_text import checked_response_text
from .rights_responses import complete_response_read, current_response_actor
from .rights_scope import locked_case
from .rights_verification import authorized_proof, complete_read


def digest(value):
    return fingerprint(canonical(value))


def actor(user, case, *, assigned):
    fresh_authority(user, case, user.session_version, user.mfa_version)
    fresh = User.objects.get(pk=user.pk)
    if not fresh.has_perm("safety.respond_rights_request") or not fresh.has_perm(
        "safety.review_rectification"
    ):
        raise PermissionDenied
    if assigned:
        current_response_actor(user, case, user.session_version, user.mfa_version, execution=True)


def context(user, case_id, version, responses, *, authority, assigned=True):
    case, person, listing = locked_case(case_id, lock_listing=True)
    authority(case)
    if assigned and case.assigned_to_id != user.pk:
        raise PermissionDenied
    if (
        case.kind != "rectify"
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != responses
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError("Inspect current correction and responses before final response")
    proof = authorized_proof(case, person, "rectify")
    return case, person, listing, proof


@sensitive_variables()
def active_check(authority, user, case, person, proof, *, assigned):
    """Bind this caller and proof across active final-service resource waits.

    Completed-close replay uses only its entry-captured authority and historical
    ledger bindings; a resolved case cannot require a new reviewing proof.
    """
    proof_id, version, responses = proof.pk, case.version, case.response_version
    caller_id = user.pk

    @sensitive_variables()
    def check():
        authority(case)
        if assigned and case.assigned_to_id != caller_id:
            raise PermissionDenied
        if (
            case.status != "reviewing"
            or case.version != version
            or case.response_version != responses
            or authorized_proof(case, person, "rectify").pk != proof_id
        ):
            raise ValidationError("Current final correction proof required")

    return check


@sensitive_variables()
def evidence(case, person, listing, review_id, *, check_authority):
    """Prepare/draft consumers pass their original caller and active-proof guard."""
    review = (
        RightsRectificationRecipientReview.objects.select_for_update()
        .select_related(
            "assessment__inventory__execution__notification__review__proposal", "action"
        )
        .filter(pk=review_id, action__request=case, outcome="accepted")
        .first()
    )
    check_authority()
    if not review:
        raise ValidationError("Accepted independent recipient review required")
    assessment = review.assessment
    execution = assessment.inventory.execution
    proposal = execution.notification.review.proposal
    latest = (
        RightsRectificationExecution.objects.filter(action__request=case).order_by("-pk").first()
    )
    if (
        latest is None
        or latest.pk != execution.pk
        or not execution_scope_matches(
            case, person, execution, check_authority=check_authority
        )
    ):
        raise ValidationError("Current executed own-scope correction required")
    changes = checked_body(proposal.encrypted_changes)
    if (
        fingerprint(json.dumps(changes, sort_keys=True))
        != execution.notification.review.changes_digest
    ):
        raise ValidationError("Approved correction contents changed")
    if person:
        from . import (
            rectification_account,
            rectification_catalog,
            rectification_contacts,
            rectification_details,
            rectification_location,
            rectification_rates,
        )

        corrected = execution.corrected_revision
        readers = {
            "catalog": rectification_catalog.source,
            "contacts": rectification_contacts.source,
            "details": rectification_details.source,
            "location": rectification_location.source,
            "rates": rectification_rates.source,
        }
        for field, expected in changes.items():
            if field == "alias":
                actual = person.alias
            elif field == "account":
                actual = {key: rectification_account.source(
                    person, case, check_authority=check_authority
                )[key] for key in expected}
            elif field == "photos":
                from apps.mediafiles.models import Photo

                original = list(Photo.objects.filter(pk__in=expected).values_list("pk", "blob_id"))
                mapping = {str(pk): str(blob) for pk, blob in original}
                retained = {
                    str(pk): str(blob)
                    for pk, blob in execution.photo_dispositions.filter(
                        source_photo_id__in=expected, outcome="retained"
                    ).values_list("source_photo_id", "blob_id")
                }
                if mapping != retained:
                    raise ValidationError("Executed photo references changed")
                actual = (
                    list(
                        corrected.photos.filter(removed_at__isnull=True)
                        .order_by("position", "created_at", "pk")
                        .values_list("blob_id", flat=True)
                    )
                    if corrected
                    else []
                )
                if set(mapping) != set(expected) or list(map(str, actual)) != [
                    mapping[key] for key in expected
                ]:
                    raise ValidationError("Executed photo selection changed")
                continue
            elif corrected is None:
                raise ValidationError("Executed corrected revision required")
            elif field in readers:
                actual = readers[field](corrected)
                if field == "details" and set(expected) == rectification_details.LEGACY_FIELDS:
                    # Historical changes did not select the later optional label.
                    actual = {key: actual[key] for key in expected}
            else:
                actual = getattr(corrected, field)
            if canonical(actual) != canonical(expected):
                raise ValidationError("Executed correction values changed")
        if "contacts" in changes:
            claim = rectification_contacts.claim(changes["contacts"], person)
            check_authority()
            if person.phone_claim_id != (claim.pk if claim else None):
                raise ValidationError("Executed contact binding changed")
        if corrected and (
            corrected.listing_id != listing.pk
            or corrected.manager_version != person.manager_version
        ):
            raise ValidationError("Corrected publication scope changed")
    data = snapshot(person, execution, case, check_authority=check_authority)
    source = fingerprint(json.dumps(data, sort_keys=True))
    decisions = validate_decisions(data, checked_body(assessment.encrypted_decisions))
    if (
        source != assessment.source_digest
        or source != review.source_digest
        or source != assessment.inventory.source_digest
        or fingerprint(json.dumps(decisions, sort_keys=True)) != review.decisions_digest
        or digest(checked_body(assessment.inventory.encrypted_inventory)) != digest(data)
    ):
        raise ValidationError("Recipient evidence or reviewed decisions changed")
    return {
        "execution": execution.pk,
        "recipient_review": review.pk,
        "recipient_source": source,
        "recipient_decisions": review.decisions_digest,
        "changes": changes,
        "publication_status": listing.status if listing else None,
        "corrected_revision_status": execution.corrected_revision.status
        if execution.corrected_revision
        else None,
        "pending": any(value["outcome"] == "pending" for value in decisions.values()),
        "recipient_outcomes": {
            outcome: sum(value["outcome"] == outcome for value in decisions.values())
            for outcome in sorted({value["outcome"] for value in decisions.values()})
        },
    }


def record(user, case, key, operation, body, *, check_authority):
    """All four active services check again before ledger access or creation."""
    signature = digest(body)
    previous = RightsAction.objects.filter(key=key).first()
    check_authority()
    if previous:
        if (
            previous.request_id,
            previous.actor_id,
            previous.operation,
            previous.payload_digest,
        ) != (case.pk, user.pk, operation, signature):
            raise ValidationError("Conflicting final correction key")
        if digest(checked_body(previous.encrypted_reason)) != signature:
            raise ValidationError("Final correction action integrity mismatch")
        return previous
    return RightsAction.objects.create(
        key=key,
        request=case,
        actor=user,
        expected_version=case.version,
        operation=operation,
        payload_digest=signature,
        encrypted_reason=seal(body),
    )


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, version, responses, recipient_review_id, key, reason, text, confirmed):
    authority = capture_authority(user, review=True, respond=True)
    checked_response_text(reason, text, confirmed)
    case, person, listing, proof = context(
        user, case_id, version, responses, authority=authority
    )
    check = active_check(authority, user, case, person, proof, assigned=True)
    material = evidence(case, person, listing, recipient_review_id, check_authority=check)
    return record(
        user,
        case,
        key,
        "rectify_final_draft",
        {
            "schema": "rectification-final-v1",
            "version": version,
            "responses": responses,
            "proof": str(proof.pk),
            "channel": case.receipt_digest,
            "session": user.session_version,
            "mfa": user.mfa_version,
            "evidence": material,
            "reason": reason,
            "text": text,
        },
        check_authority=check,
    )


@sensitive_variables()
def draft_context(
    user, case_id, version, responses, draft_id, *, authority, assigned, check_authority=None
):
    case, person, listing, proof = context(
        user, case_id, version, responses, authority=authority, assigned=assigned
    )
    if check_authority is None:
        check_authority = active_check(authority, user, case, person, proof, assigned=assigned)
    draft = (
        RightsAction.objects.select_for_update()
        .filter(
            pk=draft_id, request=case, operation="rectify_final_draft", expected_version=version
        )
        .select_related("actor")
        .first()
    )
    check_authority()
    if not draft:
        raise ValidationError("Current final response draft required")
    latest = (
        RightsAction.objects.filter(
            request=case, operation="rectify_final_draft", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if not latest or latest.pk != draft.pk:
        raise ValidationError("Latest final correction draft required")
    body = checked_body(draft.encrypted_reason)
    actor(draft.actor, case, assigned=True)
    fresh_authority(draft.actor, case, body["session"], body["mfa"])
    if (
        digest(body) != draft.payload_digest
        or body["version"] != version
        or body["responses"] != responses
        or body["proof"] != str(proof.pk)
        or body["channel"] != case.receipt_digest
        or timezone.now() >= draft.created_at + timedelta(hours=24)
        or canonical(
            evidence(
                case, person, listing, body["evidence"]["recipient_review"],
                check_authority=check_authority,
            )
        )
        != canonical(body["evidence"])
    ):
        raise ValidationError("Final correction draft changed or expired")
    return case, draft, body, proof


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, version, responses, draft_id, purpose):
    authority = capture_authority(user, review=True, respond=True)
    case, person, _, proof = context(
        user, case_id, version, responses, authority=authority, assigned=False
    )
    check = active_check(authority, user, case, person, proof, assigned=False)
    draft = RightsAction.objects.filter(
        pk=draft_id, request=case, operation="rectify_final_draft", expected_version=version
    ).first()
    if not draft:
        raise ValidationError("Current final response draft required")
    if user.pk == draft.actor_id:
        raise PermissionDenied("Independent reviewer required")
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited access purpose required")
    read = record(
        user,
        case,
        uuid.uuid4(),
        "rectify_final_read",
        {
            "draft": draft.pk,
            "digest": draft.payload_digest,
            "proof": str(proof.pk),
            "responses": responses,
            "purpose": purpose,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
        check_authority=check,
    )
    _, _, body, _ = draft_context(
        user, case_id, version, responses, draft_id,
        authority=authority, assigned=False, check_authority=check,
    )
    check()
    return read, body


@transaction.atomic
@sensitive_variables()
def review(user, case_id, version, responses, draft_id, read_id, key, outcome, reason):
    authority = capture_authority(user, review=True, respond=True)
    case, draft, body, proof = draft_context(
        user, case_id, version, responses, draft_id, authority=authority, assigned=False
    )
    check = active_check(
        authority, user, case, case.person if case.person_id else None, proof, assigned=False
    )
    if user.pk == draft.actor_id:
        raise PermissionDenied("Independent reviewer required")
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=user,
        operation="rectify_final_read",
        expected_version=version,
    ).first()
    if not read or outcome not in {"approved", "rejected"} or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Independent audited motivated final review required")
    inspected = checked_body(read.encrypted_reason)
    if (
        digest(inspected) != read.payload_digest
        or inspected["draft"] != draft.pk
        or inspected["digest"] != draft.payload_digest
        or inspected["proof"] != str(proof.pk)
    ):
        raise ValidationError("Current exact final response read required")
    fresh_authority(user, case, inspected["session"], inspected["mfa"])
    actor(user, case, assigned=False)
    return record(
        user,
        case,
        key,
        "rectify_final_review",
        {
            "draft": draft.pk,
            "digest": draft.payload_digest,
            "read": read.pk,
            "proof": str(proof.pk),
            "outcome": outcome,
            "reason": reason,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
        check_authority=check,
    )


@transaction.atomic
@sensitive_variables()
def close(user, case_id, version, responses, review_id, key):
    authority = capture_authority(user, review=True, respond=True)
    case, _, _ = locked_case(case_id, lock_listing=True)
    authority(case)
    actor(user, case, assigned=True)
    previous = RightsResponse.objects.filter(key=key).first()
    if previous:
        closure = RightsAction.objects.filter(
            key=key, request=case, actor=user, operation="rectify_final_close"
        ).first()
        if not closure or previous.request_id != case.pk or previous.actor_id != user.pk:
            raise ValidationError("Conflicting final response key")
        authority(case)
        closed = checked_body(closure.encrypted_reason)
        if (
            digest(closed) != closure.payload_digest
            or any(
                closed.get(field) != value
                for field, value in {
                    "review": review_id,
                    "version": version,
                    "responses": responses,
                    "channel": case.receipt_digest,
                }.items()
            )
            or digest(checked_body(previous.encrypted_response)) != closed.get("response_digest")
            or previous.payload_digest != closed.get("draft_digest")
            or previous.case_version != version
            or previous.response_version != responses + 1
            or case.status != "resolved"
            or previous.kind != "rectify_complete"
            or case.version != version + 1
            or case.response_version != responses + 1
        ):
            raise ValidationError("Final correction replay binding changed")
        historical_review = (
            RightsAction.objects.select_related("actor")
            .filter(pk=review_id, request=case, operation="rectify_final_review")
            .first()
        )
        historical_draft = (
            RightsAction.objects.select_related("actor")
            .filter(
                pk=closed.get("draft"), request=case, actor=user, operation="rectify_final_draft"
            )
            .first()
        )
        if not historical_review or not historical_draft:
            raise ValidationError("Final correction replay evidence unavailable")
        authority(case)
        review_body = checked_body(historical_review.encrypted_reason)
        draft_body = checked_body(historical_draft.encrypted_reason)
        if (
            digest(review_body) != closed.get("review_digest")
            or historical_review.payload_digest != closed.get("review_digest")
            or digest(draft_body) != closed.get("draft_digest")
            or historical_draft.payload_digest != closed.get("draft_digest")
            or review_body["outcome"] != "approved"
            or review_body["draft"] != historical_draft.pk
            or review_body["digest"] != historical_draft.payload_digest
            or historical_review.actor_id == user.pk
        ):
            raise ValidationError("Final correction replay review changed")
        fresh_authority(user, case, draft_body["session"], draft_body["mfa"])
        fresh_authority(historical_review.actor, case, review_body["session"], review_body["mfa"])
        actor(historical_review.actor, case, assigned=False)
        return previous
    case, person, _, proof = context(
        user, case_id, version, responses, authority=authority
    )
    check = active_check(authority, user, case, person, proof, assigned=True)
    accepted = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(
            pk=review_id, request=case, operation="rectify_final_review", expected_version=version
        )
        .first()
    )
    check()
    if not accepted:
        raise ValidationError("Independent final review required")
    latest_review = (
        RightsAction.objects.filter(
            request=case, operation="rectify_final_review", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if latest_review.pk != accepted.pk:
        raise ValidationError("Latest final response review required")
    approval = checked_body(accepted.encrypted_reason)
    if digest(approval) != accepted.payload_digest or approval["outcome"] != "approved":
        raise ValidationError("Approved intact final response required")
    case, draft, body, proof = draft_context(
        user, case_id, version, responses, approval["draft"],
        authority=authority, assigned=True, check_authority=check,
    )
    if (
        accepted.actor_id == draft.actor_id
        or draft.actor_id != user.pk
        or approval["digest"] != draft.payload_digest
        or approval["proof"] != str(proof.pk)
    ):
        raise ValidationError("Independent exact final response approval required")
    audited = RightsAction.objects.filter(
        pk=approval["read"],
        request=case,
        actor=accepted.actor,
        operation="rectify_final_read",
        expected_version=version,
    ).first()
    if not audited:
        raise ValidationError("Approved response audit unavailable")
    read_body = checked_body(audited.encrypted_reason)
    if (
        digest(read_body) != audited.payload_digest
        or read_body["draft"] != draft.pk
        or read_body["digest"] != draft.payload_digest
        or read_body["proof"] != str(proof.pk)
    ):
        raise ValidationError("Approved response audit changed")
    fresh_authority(accepted.actor, case, read_body["session"], read_body["mfa"])
    fresh_authority(accepted.actor, case, approval["session"], approval["mfa"])
    actor(accepted.actor, case, assigned=False)
    if body["evidence"]["pending"]:
        raise ValidationError("Unresolved recipient decisions prevent complete rectification")
    response_body = {
        "text": body["text"],
        "simulation": True,
        "rectification": {
            field: body["evidence"][field]
            for field in ["publication_status", "corrected_revision_status", "recipient_outcomes"]
        },
    }
    record(
        user,
        case,
        key,
        "rectify_final_close",
        {
            "review": review_id,
            "version": version,
            "responses": responses,
            "draft": draft.pk,
            "draft_digest": draft.payload_digest,
            "review_digest": accepted.payload_digest,
            "response_digest": digest(response_body),
            "channel": case.receipt_digest,
        },
        check_authority=check,
    )
    response = RightsResponse.objects.create(
        key=key,
        request=case,
        actor=user,
        case_version=version,
        response_version=responses + 1,
        kind="rectify_complete",
        payload_digest=draft.payload_digest,
        encrypted_reason=seal({"reason": body["reason"]}),
        encrypted_response=seal(response_body),
    )
    draft.final_response = response
    draft.save(update_fields=["final_response"])
    check()
    contact = unseal(case.encrypted_payload).get("email")
    if contact:
        RightsNotice.objects.create(
            response=response,
            encrypted_payload=seal(
                {
                    "recipient": contact,
                    "subject": "Respuesta privada / Private response",
                    "body": "Hay una respuesta disponible en tu acuse privado. A response is available in your private receipt.",
                }
            ),
        )
    case.version += 1
    case.response_version += 1
    case.status = "resolved"
    case.scope_status = "unverified"
    case.save(update_fields=["version", "response_version", "status", "scope_status"])
    return response
