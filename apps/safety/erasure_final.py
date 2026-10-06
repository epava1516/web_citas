"""Final erasure outcome material, anchored to the existing execution receipt.

This module is being integrated into the response/review/issuance flow. A
recorded execution is not proof of physical deletion or complete coverage.
"""

from functools import partial

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import AccountToken, PhoneChallenge, RecoveryCode, RepresentationInvitation
from apps.listings.models import Favorite, Rate
from apps.mediafiles.models import Blob, Photo
from scripts.recovery_ledger import LedgerIntegrityError
from scripts.recovery_receipts import validate_receipt

from . import rights_final_response as final_response
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


def _projection(material, text):
    pending = bool(
        material["pending_execution_purposes"]
        or material["remaining_decisions"]
        or material["operational_pending"]
    )
    # Only purpose/status/date summaries reach the requester. Legal notes, paths,
    # resource identifiers and third-party evidence remain in the private ledger.
    response_body = {
        "text": text,
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
    return pending, response_body


_POLICY = final_response.Policy(
    kinds=("erase",),
    prefix="erase",
    schema="erasure-final-draft-v1",
    execution_model=ErasureExecution,
    snapshot=snapshot,
    projection=_projection,
)
_actor = partial(final_response._actor, _POLICY)
prepare = partial(final_response.prepare, _POLICY)
inspect = partial(final_response.inspect, _POLICY)
review = partial(final_response.review, _POLICY)
issue = partial(final_response.issue, _POLICY)
