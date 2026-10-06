"""Final erasure outcome material, anchored to the existing execution receipt.

This module is being integrated into the response/review/issuance flow. A
recorded execution is not proof of physical deletion or complete coverage.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import AccountToken, PhoneChallenge, RecoveryCode, RepresentationInvitation
from apps.listings.models import Favorite, Rate
from apps.mediafiles.models import Blob, Photo
from scripts.recovery_ledger import LedgerIntegrityError
from scripts.recovery_receipts import validate_receipt

from .erasure_inventory import canonical
from .models import ErasureExecution, RecoveryOutbox, RightsExport
from .recovery_ownership import validate_ownership
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_verification import PROCEDURE, enabled


@sensitive_variables()
def snapshot(case, person, listing, execution_id):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Final erasure material requires canonical scope locks")
    execution = (
        ErasureExecution.objects.select_for_update(of=("self",))
        .select_related("action", "proof", "plan__inventory", "plan__action")
        .filter(
            pk=execution_id,
            action__request=case,
            person=person,
            account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if not execution or case.kind != "erase":
        raise ValidationError("Executed own-scope erasure required")
    proof, plan = execution.proof, execution.plan
    if (
        not enabled()
        or proof.request_id != case.pk
        or proof.scope != "erase"
        or proof.status != "passed"
        or proof.provider != "simulator"
        or proof.procedure != PROCEDURE
        or proof.channel_digest != case.receipt_digest
        or proof.person_id != (person.pk if person else None)
        or proof.account_subject_id != case.account_subject_id
        or proof.expires_at <= timezone.now()
        or case.receipt_expires_at <= timezone.now()
        or plan.action.request_id != case.pk
        or plan.inventory.proof_id != proof.pk
        or plan.inventory.person_id != execution.person_id
        or plan.inventory.account_subject_id != execution.account_subject_id
        or proof.case_version != execution.action.expected_version
    ):
        raise ValidationError("Original scoped authorization unavailable or expired")
    outbox = RecoveryOutbox.objects.select_for_update().filter(execution=execution).first()
    if not outbox:
        raise ValidationError("Transactional execution receipt required")
    receipt = checked_body(outbox.encrypted_event)
    result = checked_body(execution.encrypted_result)
    manifest = checked_body(plan.inventory.encrypted_manifest)
    decisions = checked_body(plan.encrypted_decisions)
    try:
        validate_receipt(receipt)
        if (
            receipt["execution"] != str(execution.pk)
            or receipt["subject"] != str(case.account_subject_id if person is None else person.pk)
            or receipt["scope"] != ("account" if person is None else "person")
            or receipt["purposes"] != result["executed_purposes"]
            or receipt["pending_purposes"] != result["pending_purposes"]
            or fingerprint(canonical(manifest)) != plan.source_digest
            or plan.source_digest != plan.inventory.source_digest
            or decisions.get("schema") != "erasure-plan-v1"
            or fingerprint(
                canonical(
                    {
                        "inventory": str(plan.inventory_id),
                        "version": plan.action.expected_version,
                        "decisions": decisions["decisions"],
                    }
                )
            )
            != plan.action.payload_digest
        ):
            raise ValueError
        validate_ownership(receipt)
    except (LedgerIntegrityError, KeyError, TypeError, ValueError) as error:
        raise ValidationError("Erasure outcome receipt or scope changed") from error
    refs = receipt["references"]
    if person and (
        person.rights_version != refs["person"]["minimum_rights_version"]
        or person.manager_version != refs["person"]["minimum_manager_version"]
    ):
        raise ValidationError("Profile changed after this erasure execution")
    subject = case.account_subject if person is None else person.subject
    checks = {}
    selected = set(receipt["purposes"])
    if selected & {"account", "authentication", "account_preferences"}:
        anchor = refs.get("account")
        if not subject or not anchor or anchor["id"] != str(subject.pk):
            raise ValidationError("Executed subject account required")
        if (
            subject.session_version < anchor["minimum_session_version"]
            or subject.mfa_version < anchor["minimum_mfa_version"]
        ):
            raise ValidationError("Revoked account capabilities reintroduced")
    if "authentication" in selected:
        checks["authentication"] = not (
            AccountToken.objects.filter(user=subject).exists()
            or RecoveryCode.objects.filter(user=subject).exists()
        )
    if "account_preferences" in selected:
        checks["account_preferences"] = not Favorite.objects.filter(user=subject).exists()
    if "account" in selected:
        checks["account"] = bool(
            subject.account_erased_at
            and not subject.is_active
            and not subject.first_name
            and not subject.last_name
            and not subject.email_verified_at
            and not subject.last_login
            and not subject.mfa_enabled
            and not subject.mfa_secret_encrypted
            and not subject.has_usable_password()
            and subject.username.startswith("erased-")
            and subject.email.endswith("@example.invalid")
        )
    if "contact" in selected:
        checks["contact"] = not PhoneChallenge.objects.filter(person=person).exists()
    if "representation" in selected:
        checks["representation"] = (
            bool(
                person.consent_revoked_at
                and person.age_status == "pending"
                and (not listing or listing.status != "published")
            )
            and not RepresentationInvitation.objects.filter(person=person).exists()
        )
    if "shared_contact_review" in selected:
        checks["shared_contact_review"] = person.phone_claim_id is None and not (
            listing and listing.revisions.exclude(phone="", whatsapp=False, telegram="").exists()
        )
    if "profile" in selected:
        checks["profile"] = not person.alias and not person.assigned_editor_id
    if "publication" in selected:
        revisions = listing.revisions.all() if listing else None
        checks["publication"] = bool(person.publication_erased_at) and (
            listing is None
            or (
                listing.status == "withdrawn"
                and listing.approved_revision_id is None
                and not listing.available_until
                and not listing.published_at
                and not listing.expires_at
                and not revisions.exclude(
                    status="withdrawn",
                    title="",
                    description="",
                    description_alternative="",
                    phone="",
                    whatsapp=False,
                    telegram="",
                    municipality=None,
                    postal_code=None,
                    zone=None,
                    profile_type="",
                    spoken_languages=[],
                    days=[],
                    time_slot="",
                    reception=False,
                    travel=False,
                    contact_exposure_accepted=False,
                ).exists()
                and not Rate.objects.filter(revision__listing=listing).exists()
                and not revisions.filter(categories__isnull=False).exists()
                and not revisions.filter(services__isnull=False).exists()
                and not revisions.filter(travel_areas__isnull=False).exists()
            )
        )
    if "transient_copy" in selected:
        copies = RightsExport.objects.filter(
            person=person, account_subject_id=case.account_subject_id
        )
        checks["transient_copy"] = (
            not copies.exclude(encrypted_payload="").exists()
            and not copies.filter(purged_at__isnull=True).exists()
            and not copies.filter(images__encrypted_content__gt="").exists()
            and not copies.filter(parts__encrypted_content__gt="").exists()
        )
    if "media" in selected:
        complete = not Photo.objects.filter(
            revision__listing__person=person, removed_at__isnull=True
        ).exists()
        for reference in refs.get("media_jobs", []):
            job = (
                execution.media_jobs.select_related("blob")
                .filter(pk=reference["job"], blob_id=reference["blob"])
                .first()
            )
            if (
                not job
                or job.status != "completed"
                or not job.completed_at
                or job.blob.status != "erased"
                or job.blob.original
                or job.blob.derivative
            ):
                complete = False
            for field, path in reference["paths"].items():
                if path and Blob._meta.get_field(field).storage.exists(path):
                    complete = False
        if refs["resources"]["media_operation"] == "detach_shared_and_review_exclusive":
            original_exclusive = [
                row["blob"] for row in refs["resources"]["photos"] if not row["shared"]
            ]
            complete = (
                complete
                and not Blob.objects.filter(pk__in=original_exclusive)
                .exclude(status="erased", original="", derivative="")
                .exists()
            )
        checks["media"] = complete
    return {
        "schema": "erasure-final-material-v1",
        "execution": str(execution.pk),
        "proof": str(proof.pk),
        "plan_digest": fingerprint(plan.encrypted_decisions),
        "execution_digest": fingerprint(execution.encrypted_result),
        "receipt_digest": fingerprint(canonical(receipt)),
        "completed_purposes": sorted(p for p, complete in checks.items() if complete),
        "pending_execution_purposes": sorted(p for p, complete in checks.items() if not complete),
        "remaining_decisions": [
            row for row in decisions["decisions"] if row["purpose"] not in selected
        ],
        "operational_pending": manifest.get("pending", []),
        "identity_simulated": True,
    }


def _actor(user, case, *, assigned):
    from django.core.exceptions import PermissionDenied

    from apps.core.models import User

    from .rights_copy_page_review import fresh_authority

    fresh_authority(user, case, user.session_version, user.mfa_version)
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.has_perm("safety.respond_rights_request")
        or (assigned and case.assigned_to_id != fresh.pk)
    ):
        raise PermissionDenied


def _context(user, case_id, version, responses, *, assigned):
    from .rights_responses import complete_response_read
    from .rights_scope import locked_case
    from .rights_verification import complete_read

    case, person, listing = locked_case(case_id, lock_listing=True, allow_erased_account=True)
    _actor(user, case, assigned=assigned)
    if (
        case.kind != "erase"
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != responses
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError("Inspect current erasure case and outgoing responses")
    return case, person, listing


def _digest(body):
    return fingerprint(canonical(body))


def _record(user, case, key, operation, body):
    from .crypto import seal
    from .models import RightsAction

    signature = _digest(body)
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id,
            previous.actor_id,
            previous.operation,
            previous.payload_digest,
        ) != (case.pk, user.pk, operation, signature):
            raise ValidationError("Conflicting final erasure action key")
        if _digest(checked_body(previous.encrypted_reason)) != signature:
            raise ValidationError("Final erasure action integrity changed")
        return previous
    return RightsAction.objects.create(
        key=key,
        request=case,
        actor=user,
        operation=operation,
        expected_version=case.version,
        payload_digest=signature,
        encrypted_reason=seal(body),
    )


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, version, responses, execution_id, key, reason, text, confirmed):
    from .rights_response_text import checked_response_text

    checked_response_text(reason, text, confirmed)
    case, person, listing = _context(user, case_id, version, responses, assigned=True)
    material = snapshot(case, person, listing, execution_id)
    latest = ErasureExecution.objects.filter(action__request=case).order_by("-action_id").first()
    if not latest or str(latest.pk) != str(execution_id):
        raise ValidationError("Latest own-scope erasure execution required")
    return _record(
        user,
        case,
        key,
        "erase_final_draft",
        {
            "schema": "erasure-final-draft-v1",
            "version": version,
            "responses": responses,
            "channel": case.receipt_digest,
            "session": user.session_version,
            "mfa": user.mfa_version,
            "material": material,
            "reason": reason,
            "text": text,
        },
    )


def _draft(user, case_id, version, responses, draft_id, *, assigned):
    from datetime import timedelta

    from .models import RightsAction
    from .rights_copy_page_review import fresh_authority

    case, person, listing = _context(user, case_id, version, responses, assigned=assigned)
    draft = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(pk=draft_id, request=case, operation="erase_final_draft", expected_version=version)
        .first()
    )
    latest = (
        RightsAction.objects.filter(
            request=case, operation="erase_final_draft", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if not draft or not latest or latest.pk != draft.pk:
        raise ValidationError("Latest final erasure draft required")
    body = checked_body(draft.encrypted_reason)
    _actor(draft.actor, case, assigned=True)
    fresh_authority(draft.actor, case, body["session"], body["mfa"])
    latest_execution = (
        ErasureExecution.objects.filter(action__request=case).order_by("-action_id").first()
    )
    if (
        _digest(body) != draft.payload_digest
        or body["version"] != version
        or body["responses"] != responses
        or body["channel"] != case.receipt_digest
        or timezone.now() >= draft.created_at + timedelta(hours=24)
        or not latest_execution
        or str(latest_execution.pk) != body["material"]["execution"]
        or canonical(snapshot(case, person, listing, body["material"]["execution"]))
        != canonical(body["material"])
    ):
        raise ValidationError("Final erasure draft or execution changed or expired")
    return case, draft, body


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, version, responses, draft_id, purpose):
    import uuid

    from django.core.exceptions import PermissionDenied

    from .models import RightsAction

    case, _, _ = _context(user, case_id, version, responses, assigned=False)
    draft = RightsAction.objects.filter(
        pk=draft_id, request=case, operation="erase_final_draft", expected_version=version
    ).first()
    if not draft:
        raise ValidationError("Current final erasure draft required")
    if draft.actor_id == user.pk:
        raise PermissionDenied("Independent reviewer required")
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited access purpose required")
    read = _record(
        user,
        case,
        uuid.uuid4(),
        "erase_final_read",
        {
            "draft": draft.pk,
            "digest": draft.payload_digest,
            "responses": responses,
            "channel": case.receipt_digest,
            "purpose": purpose,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    _, _, body = _draft(user, case_id, version, responses, draft_id, assigned=False)
    return read, body


@transaction.atomic
@sensitive_variables()
def review(user, case_id, version, responses, draft_id, read_id, key, outcome, reason):
    from django.core.exceptions import PermissionDenied

    from .models import RightsAction
    from .rights_copy_page_review import fresh_authority

    case, draft, _ = _draft(user, case_id, version, responses, draft_id, assigned=False)
    if user.pk == draft.actor_id:
        raise PermissionDenied("Independent reviewer required")
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=user,
        operation="erase_final_read",
        expected_version=version,
    ).first()
    if (
        not read
        or outcome not in {"approved", "rejected"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Independent audited motivated review required")
    inspected = checked_body(read.encrypted_reason)
    if (
        _digest(inspected) != read.payload_digest
        or inspected["draft"] != draft.pk
        or inspected["digest"] != draft.payload_digest
        or inspected["responses"] != responses
        or inspected["channel"] != case.receipt_digest
    ):
        raise ValidationError("Exact current final erasure read required")
    fresh_authority(user, case, inspected["session"], inspected["mfa"])
    return _record(
        user,
        case,
        key,
        "erase_final_review",
        {
            "draft": draft.pk,
            "digest": draft.payload_digest,
            "read": read.pk,
            "outcome": outcome,
            "reason": reason,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )


@transaction.atomic
@sensitive_variables()
def issue(user, case_id, version, responses, review_id, key):
    from .crypto import seal, unseal
    from .models import RightsAction, RightsNotice, RightsResponse
    from .rights_copy_page_review import fresh_authority
    from .rights_scope import locked_case

    case, _, _ = locked_case(case_id, lock_listing=True, allow_erased_account=True)
    _actor(user, case, assigned=True)
    previous = RightsResponse.objects.filter(key=key).first()
    if previous:
        issuance = RightsAction.objects.filter(
            key=key, request=case, actor=user, operation="erase_final_issue"
        ).first()
        if not issuance or previous.request_id != case.pk or previous.actor_id != user.pk:
            raise ValidationError("Conflicting final erasure response key")
        issued = checked_body(issuance.encrypted_reason)
        if (
            _digest(issued) != issuance.payload_digest
            or issued.get("review") != review_id
            or issued.get("version") != version
            or issued.get("responses") != responses
            or issued.get("channel") != case.receipt_digest
            or _digest(checked_body(previous.encrypted_response)) != issued.get("response_digest")
            or previous.payload_digest != issued.get("draft_digest")
            or previous.case_version != version
            or previous.response_version != responses + 1
            or previous.kind != issued.get("kind")
        ):
            raise ValidationError("Final erasure replay binding changed")
        draft = (
            RightsAction.objects.select_related("actor")
            .filter(pk=issued.get("draft"), request=case, actor=user, operation="erase_final_draft")
            .first()
        )
        approval = (
            RightsAction.objects.select_related("actor")
            .filter(pk=review_id, request=case, operation="erase_final_review")
            .first()
        )
        if not draft or not approval or approval.actor_id == user.pk:
            raise ValidationError("Final erasure replay evidence unavailable")
        body, decision = (
            checked_body(draft.encrypted_reason),
            checked_body(approval.encrypted_reason),
        )
        if (
            _digest(body) != draft.payload_digest
            or draft.payload_digest != issued.get("draft_digest")
            or _digest(decision) != approval.payload_digest
            or approval.payload_digest != issued.get("review_digest")
            or decision.get("outcome") != "approved"
            or decision.get("draft") != draft.pk
            or decision.get("digest") != draft.payload_digest
        ):
            raise ValidationError("Final erasure replay approval changed")
        fresh_authority(user, case, body["session"], body["mfa"])
        fresh_authority(approval.actor, case, decision["session"], decision["mfa"])
        _actor(approval.actor, case, assigned=False)
        return previous
    approval = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(
            pk=review_id, request=case, operation="erase_final_review", expected_version=version
        )
        .first()
    )
    latest = (
        RightsAction.objects.filter(
            request=case, operation="erase_final_review", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if not approval or not latest or latest.pk != approval.pk:
        raise ValidationError("Latest independent final erasure review required")
    decision = checked_body(approval.encrypted_reason)
    if _digest(decision) != approval.payload_digest or decision.get("outcome") != "approved":
        raise ValidationError("Intact approved final erasure response required")
    case, draft, body = _draft(user, case_id, version, responses, decision["draft"], assigned=True)
    if (
        draft.actor_id != user.pk
        or approval.actor_id == user.pk
        or decision["digest"] != draft.payload_digest
    ):
        raise ValidationError("Independent exact final erasure approval required")
    read = RightsAction.objects.filter(
        pk=decision["read"],
        request=case,
        actor=approval.actor,
        operation="erase_final_read",
        expected_version=version,
    ).first()
    if not read:
        raise ValidationError("Final erasure audit unavailable")
    inspected = checked_body(read.encrypted_reason)
    if (
        _digest(inspected) != read.payload_digest
        or inspected["draft"] != draft.pk
        or inspected["digest"] != draft.payload_digest
        or inspected["responses"] != responses
        or inspected["channel"] != case.receipt_digest
    ):
        raise ValidationError("Final erasure audit changed")
    fresh_authority(approval.actor, case, inspected["session"], inspected["mfa"])
    fresh_authority(approval.actor, case, decision["session"], decision["mfa"])
    _actor(approval.actor, case, assigned=False)
    material = body["material"]
    pending = bool(
        material["pending_execution_purposes"]
        or material["remaining_decisions"]
        or material["operational_pending"]
    )
    kind = "erase_partial" if pending else "erase_complete"
    # Only purpose/status/date summaries reach the requester. Legal notes, paths,
    # resource identifiers and third-party evidence remain in the private ledger.
    response_body = {
        "text": body["text"],
        "simulation": True,
        "erasure": {
            "complete": not pending,
            "completed_purposes": material["completed_purposes"],
            "pending_execution_purposes": material["pending_execution_purposes"],
            "remaining_decisions": [
                {field: row.get(field) for field in ["purpose", "operation", "review_on"]}
                for row in material["remaining_decisions"]
            ],
            "operational_pending": material["operational_pending"],
        },
    }
    _record(
        user,
        case,
        key,
        "erase_final_issue",
        {
            "review": review_id,
            "version": version,
            "responses": responses,
            "draft": draft.pk,
            "draft_digest": draft.payload_digest,
            "review_digest": approval.payload_digest,
            "response_digest": _digest(response_body),
            "channel": case.receipt_digest,
            "kind": kind,
        },
    )
    response = RightsResponse.objects.create(
        key=key,
        request=case,
        actor=user,
        case_version=version,
        response_version=responses + 1,
        kind=kind,
        payload_digest=draft.payload_digest,
        encrypted_reason=seal({"reason": body["reason"]}),
        encrypted_response=seal(response_body),
    )
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
    case.scope_status = "unverified"
    if not pending:
        case.status = "resolved"
    case.save(update_fields=["version", "response_version", "scope_status", "status"])
    return response
