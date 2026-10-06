"""Scoped, audited erasure inventory. Preparation never deletes or closes a request."""

import json
import uuid

from django import forms
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import Agency, AgencyMember, Person
from apps.mediafiles.models import Blob, Photo

from .crypto import seal, unseal
from .models import ErasureInventory, RightsAction, RightsRequest
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private


def canonical(value):
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)


@sensitive_variables()
def source_manifest(person, case=None):
    if case and case.account_subject_id:
        from .account_erasure_inventory import source

        return source(case)
    subject = person.subject_id
    profile = "revision__listing__person"
    scopes = [
        ("core.Person", Q(pk=person.pk), "profile", None),
        ("listings.Listing", Q(person=person), "publication", None),
        (
            "core.PhoneClaim",
            Q(pk=person.phone_claim_id),
            "shared_contact_review",
            ["pk", "phone", "verified_at", "verification_procedure"],
        ),
        ("listings.Revision", Q(listing__person=person), "publication", None),
        ("listings.Rate", Q(revision__listing__person=person), "publication", None),
        ("mediafiles.Photo", Q(**{profile: person}), "media", None),
        (
            "safety.RightsRectificationPhotoUpload",
            Q(photo__revision__listing__person=person),
            "media",
            [
                "pk",
                "photo_id",
                "action_id",
                "proof_id",
                "source_digest",
                "person_rights_version",
                "expires_at",
                "discarded_at",
                "created_at",
            ],
        ),
        (
            "mediafiles.MediaPreparationCleanup",
            Q(blob__photos__revision__listing__person=person),
            "media",
            [
                "pk",
                "blob_id",
                "status",
                "reason_code",
                "attempts",
                "next_attempt_at",
                "completed_at",
                "created_at",
            ],
        ),
        (
            "mediafiles.MediaErasure",
            Q(execution__person=person),
            "media",
            [
                "pk",
                "blob_id",
                "status",
                "attempts",
                "next_attempt_at",
                "completed_at",
                "recovery_version",
            ],
        ),
        (
            "mediafiles.UploadAttempt",
            Q(**{profile: person}),
            "media",
            ["pk", "result", "created_at"],
        ),
        (
            "mediafiles.Match",
            Q(photo__revision__listing__person=person)
            | Q(candidate__revision__listing__person=person),
            "evidence",
            ["pk", "decision", "review_version", "resolved_at"],
        ),
        (
            "mediafiles.PhotoRestriction",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "reason_code"],
        ),
        (
            "mediafiles.PhotoAppeal",
            Q(restriction__person=person),
            "evidence",
            ["pk", "status", "result", "resolved_at"],
        ),
        (
            "core.PhoneChallenge",
            Q(person=person),
            "contact",
            [
                "pk",
                "manager_version",
                "person_rights_version",
                "phone",
                "expires_at",
                "used_at",
                "attempts",
            ],
        ),
        (
            "core.RepresentationInvitation",
            Q(person=person),
            "representation",
            ["pk", "manager_version", "person_rights_version", "email", "expires_at", "used_at"],
        ),
        (
            "core.RepresentationAction",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "action", "created_at"],
        ),
        (
            "core.VerificationCheck",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "status", "completed_at"],
        ),
        (
            "core.VerificationEvent",
            Q(verification__person=person),
            "evidence",
            ["pk", "outcome", "created_at"],
        ),
        (
            "core.ManagerReview",
            Q(person=person),
            "evidence",
            ["pk", "manager_version", "outcome", "created_at"],
        ),
        (
            "core.ManagerAppeal",
            Q(decision__person=person),
            "evidence",
            ["pk", "status", "result", "resolved_at"],
        ),
        (
            "listings.Submission",
            Q(**{profile: person}),
            "evidence",
            ["pk", "declaration_version", "created_at"],
        ),
        (
            "listings.ModerationDecision",
            Q(**{profile: person}),
            "evidence",
            ["pk", "outcome", "created_at"],
        ),
        (
            "listings.Appeal",
            Q(decision__revision__listing__person=person),
            "evidence",
            ["pk", "status", "result", "resolved_at"],
        ),
        (
            "listings.LifecycleAction",
            Q(listing__person=person),
            "evidence",
            ["pk", "manager_version", "operation", "created_at"],
        ),
        (
            "safety.Report",
            Q(listing__person=person) | Q(reported_subject_id=subject)
            if subject
            else Q(listing__person=person),
            "third_party_evidence",
            ["pk", "version", "status"],
        ),
        ("safety.Restriction", Q(listing__person=person), "evidence", ["pk", "active"]),
        (
            "safety.RightsRequest",
            Q(person=person),
            "third_party_evidence",
            ["pk", "version", "response_version", "status"],
        ),
        (
            "safety.RightsExport",
            Q(person=person),
            "transient_copy",
            ["pk", "expires_at", "purged_at"],
        ),
        (
            "safety.RightsExportPart",
            Q(export__person=person),
            "transient_copy",
            ["pk", "export_id", "position"],
        ),
        (
            "safety.RightsExportImage",
            Q(export__person=person),
            "transient_copy",
            ["pk", "export_id"],
        ),
        (
            "safety.PrivacyPublicationHold",
            Q(person=person),
            "evidence",
            [
                "version",
                "purpose_review_on",
                "initial_purpose_review_on",
                "pk",
                "action_id",
                "proof_id",
                "active",
                "manager_version",
                "ground",
                "subject_snapshot",
                "previous_listing_status",
                "previous_lifecycle_version",
            ],
        ),
    ]
    scopes.append(
        (
            "mediafiles.MediaErasureRecovery",
            Q(job__execution__person=person),
            "dependent_evidence",
            ["pk", "action_id", "previous_version", "previous_attempts"],
        )
    )
    scopes.extend(
        [
            (
                "safety.RightsRectificationProposal",
                Q(person=person),
                "dependent_evidence",
                ["pk", "action_id", "proof_id", "source_revision_id", "created_at"],
            ),
            (
                "safety.RightsRectificationSourceRead",
                Q(request__person=person),
                "dependent_evidence",
                ["pk", "case_version", "proof_id", "created_at"],
            ),
        ]
    )
    scopes.extend(
        [
            (
                "safety.RightsRectificationProposalRead",
                Q(proposal__person=person),
                "dependent_evidence",
                ["pk", "proposal_id", "proof_id", "case_version", "created_at"],
            ),
            (
                "safety.RightsRectificationReview",
                Q(proposal__person=person),
                "dependent_evidence",
                ["pk", "proposal_id", "action_id", "proof_id", "outcome", "created_at"],
            ),
            (
                "safety.RightsRectificationNotification",
                Q(review__proposal__person=person),
                "dependent_evidence",
                ["pk", "review_id", "action_id", "response_id", "proof_id", "created_at"],
            ),
            (
                "safety.RightsRectificationExecution",
                Q(notification__review__proposal__person=person),
                "dependent_evidence",
                [
                    "pk",
                    "notification_id",
                    "action_id",
                    "proof_id",
                    "corrected_revision_id",
                    "resulting_rights_version",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccountEmailConfirmation",
                Q(proposal__person=person),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "proposal_id",
                    "proof_id",
                    "subject_id",
                    "source_digest",
                    "destination_digest",
                    "encrypted_delivery",
                    "expires_at",
                    "confirmed_at",
                    "consumed_at",
                    "revoked_at",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPhotoReintroductionRead",
                Q(candidate__photo__revision__listing__person=person),
                "dependent_evidence",
                [
                    "pk",
                    "candidate_id",
                    "actor_id",
                    "review_version",
                    "source_digest",
                    "purpose",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPhotoReintroductionDecision",
                Q(candidate__photo__revision__listing__person=person),
                "dependent_evidence",
                [
                    "pk",
                    "candidate_id",
                    "read_id",
                    "review_version",
                    "source_digest",
                    "outcome",
                    "encrypted_reason",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPhotoReintroduction",
                Q(photo__revision__listing__person=person),
                "dependent_evidence",
                [
                    "pk",
                    "photo_id",
                    "uploaded_blob_id",
                    "disposition_id",
                    "review_version",
                    "method",
                    "score",
                    "created_at",
                ],
            ),
            (
                "safety.RightsRectificationPhotoDisposition",
                Q(execution__notification__review__proposal__person=person),
                "dependent_evidence",
                ["pk", "execution_id", "source_photo_id", "blob_id", "outcome", "created_at"],
            ),
            (
                "safety.RightsRectificationManagerNotice",
                Q(execution__notification__review__proposal__person=person),
                "dependent_evidence",
                ["pk", "execution_id", "manager_version", "acknowledged_at", "created_at"],
            ),
            (
                "safety.RightsRectificationRecipientInventory",
                Q(execution__notification__review__proposal__person=person),
                "dependent_evidence",
                ["pk", "execution_id", "action_id", "proof_id", "created_at"],
            ),
            (
                "safety.RightsRectificationRecipientAssessment",
                Q(inventory__execution__notification__review__proposal__person=person),
                "dependent_evidence",
                ["pk", "inventory_id", "action_id", "proof_id", "created_at"],
            ),
            (
                "safety.RightsRectificationRecipientReview",
                Q(assessment__inventory__execution__notification__review__proposal__person=person),
                "dependent_evidence",
                ["pk", "assessment_id", "action_id", "proof_id", "outcome", "created_at"],
            ),
        ]
    )
    report_scope = Q(report__listing__person=person)
    complaint_scope = Q(decision__report__listing__person=person) | Q(
        listing_decision__revision__listing__person=person
    )
    for label, scope, fields in [
        ("safety.ReportAccess", report_scope, ["pk", "case_version", "created_at"]),
        (
            "safety.ComplaintMessage",
            Q(complaint__decision__report__listing__person=person)
            | Q(complaint__listing_decision__revision__listing__person=person),
            ["pk", "expected_version", "created_at"],
        ),
        (
            "safety.ReportAction",
            report_scope,
            ["pk", "operation", "expected_version", "created_at"],
        ),
        ("safety.ReportNotice", report_scope, ["pk", "status", "attempts", "recovery_version"]),
        (
            "safety.UrgentReportAlert",
            report_scope | Q(report__reported_subject_id=subject) if subject else report_scope,
            ["pk", "report_id", "created_at", "acknowledged_at", "acknowledged_by_id"],
        ),
        ("safety.Complaint", complaint_scope, ["pk", "version", "status"]),
        (
            "safety.ComplaintAction",
            Q(complaint__decision__report__listing__person=person)
            | Q(complaint__listing_decision__revision__listing__person=person),
            ["pk", "operation", "expected_version"],
        ),
        (
            "safety.RightsProof",
            Q(person=person),
            ["pk", "case_version", "manager_version", "scope", "status", "expires_at"],
        ),
        (
            "safety.RightsWithdrawal",
            Q(person=person),
            ["pk", "previous_manager_version", "created_at"],
        ),
        (
            "safety.RightsResponse",
            Q(request__person=person),
            ["pk", "case_version", "response_version", "kind"],
        ),
        (
            "safety.RightsNotice",
            Q(response__request__person=person),
            ["pk", "status", "attempts", "recovery_version"],
        ),
        (
            "safety.RightsResponseAcknowledgement",
            Q(response__request__person=person),
            ["pk", "response_id", "created_at"],
        ),
        (
            "safety.RightsPortabilityRead",
            Q(assessment__request__person=person),
            [
                "pk",
                "assessment_id",
                "action_id",
                "proof_id",
                "source_digest",
                "assessment_digest",
                "original_session_version",
                "original_mfa_version",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilityReview",
            Q(assessment__request__person=person),
            [
                "pk",
                "read_id",
                "outcome",
                "assessment_id",
                "action_id",
                "proof_id",
                "source_digest",
                "assessment_digest",
                "original_session_version",
                "original_mfa_version",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilitySelectionReview",
            Q(selection__request__person=person),
            [
                "pk",
                "action_id",
                "selection_id",
                "read_id",
                "outcome",
                "image_reads",
                "proof_id",
                "source_digest",
                "selection_digest",
                "original_session_version",
                "original_mfa_version",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilitySelectionRead",
            Q(selection__request__person=person),
            [
                "pk",
                "action_id",
                "selection_id",
                "proof_id",
                "source_digest",
                "selection_digest",
                "original_session_version",
                "original_mfa_version",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilitySelection",
            Q(request__person=person),
            [
                "pk",
                "action_id",
                "assessment_review_id",
                "proof_id",
                "source_digest",
                "assessment_digest",
                "inspection_digest",
                "decision_digest",
                "version",
                "original_session_version",
                "original_mfa_version",
                "selection_digest",
                "encrypted_selection",
                "expires_at",
                "purged_at",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilityAssessment",
            Q(request__person=person),
            [
                "pk",
                "action_id",
                "proof_id",
                "source_digest",
                "version",
                "original_session_version",
                "original_mfa_version",
                "encrypted_assessment",
                "expires_at",
                "purged_at",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilityCoverageReview",
            Q(coverage__request__person=person),
            [
                "pk",
                "action_id",
                "coverage_id",
                "proof_id",
                "source_digest",
                "coverage_digest",
                "original_session_version",
                "original_mfa_version",
                "read_ids",
                "outcome",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilityCoverageRead",
            Q(coverage__request__person=person),
            [
                "pk",
                "action_id",
                "coverage_id",
                "proof_id",
                "source_digest",
                "coverage_digest",
                "original_session_version",
                "original_mfa_version",
                "dataset",
                "row_index",
                "field_page",
                "binary",
                "page_digest",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilityCoverage",
            Q(request__person=person),
            [
                "pk",
                "request_id",
                "actor_id",
                "action_id",
                "selection_review_id",
                "proof_id",
                "source_digest",
                "selection_digest",
                "coverage_digest",
                "original_session_version",
                "original_mfa_version",
                "version",
                "encrypted_coverage",
                "expires_at",
                "purged_at",
                "created_at",
            ],
        ),
        (
            "safety.RightsPortabilityImageRead",
            Q(selection__request__person=person),
            [
                "pk",
                "action_id",
                "selection_id",
                "selection_read_id",
                "photo_id",
                "proof_id",
                "source_digest",
                "selection_digest",
                "content_digest",
                "original_session_version",
                "original_mfa_version",
                "created_at",
            ],
        ),
        (
            "safety.RightsExportPortabilityBinding",
            Q(export__person=person),
            [
                "pk",
                "export_id",
                "review_id",
                "source_digest",
                "selection_digest",
                "ciphertext_digest",
                "inspection_digest",
                "decision_digest",
                "payload_digest",
                "coverage_review_id",
                "coverage_use_id",
                "coverage_digest",
                "coverage_ciphertext_digest",
                "coverage_decision_digest",
                "coverage_reads_digest",
                "original_session_version",
                "original_mfa_version",
                "created_at",
            ],
        ),
        (
            "safety.RightsExportInformationBinding",
            Q(export__person=person),
            [
                "pk",
                "export_id",
                "review_id",
                "source_digest",
                "information_digest",
                "policy_digest",
                "inspection_digest",
                "decision_digest",
                "created_at",
            ],
        ),
        (
            "safety.RightsCopyInformationRead",
            Q(information__request__person=person),
            [
                "pk",
                "information_id",
                "action_id",
                "proof_id",
                "source_digest",
                "information_digest",
                "original_session_version",
                "original_mfa_version",
                "policy_digest",
                "created_at",
                "action__actor_id",
                "action__expected_version",
                "action__payload_digest",
                "action__encrypted_reason",
            ],
        ),
        (
            "safety.RightsCopyInformationReview",
            Q(information__request__person=person),
            [
                "pk",
                "information_id",
                "action_id",
                "proof_id",
                "source_digest",
                "information_digest",
                "original_session_version",
                "original_mfa_version",
                "policy_digest",
                "created_at",
                "action__actor_id",
                "action__expected_version",
                "action__payload_digest",
                "action__encrypted_reason",
                "read_id",
                "outcome",
            ],
        ),
        (
            "safety.RightsCopyInformation",
            Q(request__person=person),
            [
                "pk",
                "request_id",
                "actor_id",
                "action_id",
                "proof_id",
                "source_digest",
                "policy_version",
                "policy_document_id",
                "policy_digest",
                "original_session_version",
                "original_mfa_version",
                "version",
                "encrypted_information",
                "expires_at",
                "purged_at",
            ],
        ),
        (
            "safety.RightsCopyPageReview",
            Q(request__person=person),
            [
                "pk",
                "request_id",
                "actor_id",
                "action_id",
                "read_action_id",
                "proof_id",
                "source_digest",
                "section",
                "page",
                "version",
                "encrypted_entries",
                "expires_at",
                "purged_at",
            ],
        ),
        (
            "safety.PublicationCalendarEvent",
            Q(hold__person=person),
            [
                "pk",
                "hold_id",
                "action_id",
                "expected_version",
                "created_at",
                "action__encrypted_reason",
                "action__payload_digest",
            ],
        ),
        (
            "safety.PrivacyHoldReleaseProposal",
            Q(hold__person=person),
            [
                "pk",
                "purpose_read_id",
                "ground",
                "resume_message_id",
                "source_digest",
                "hold_id",
                "action_id",
                "response_id",
                "released_action_id",
                "released_proof_id",
                "released_at",
            ],
        ),
        (
            "safety.RightsImageAccess",
            Q(photo__revision__listing__person=person),
            ["pk", "case_version", "created_at"],
        ),
        ("safety.RightsExportDownload", Q(export__person=person), ["pk", "created_at"]),
    ]:
        scopes.append((label, scope, "dependent_evidence", fields))
    if subject:
        scopes += [
            (
                "core.User",
                Q(pk=subject),
                "account",
                [
                    "pk",
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "is_active",
                    "account_erased_at",
                    "role",
                    "session_version",
                    "mfa_version",
                ],
            ),
            (
                "core.AccountToken",
                Q(user_id=subject),
                "authentication",
                ["pk", "purpose", "expires_at", "used_at"],
            ),
            ("core.RecoveryCode", Q(user_id=subject), "authentication", ["pk", "used_at"]),
            (
                "core.LegalAcceptance",
                Q(user_id=subject),
                "evidence",
                ["pk", "document_id", "action", "created_at"],
            ),
            ("listings.Favorite", Q(user_id=subject), "account_preferences", ["pk", "created_at"]),
        ]
    entries = []
    for label, scope, purpose, fields in scopes:
        model = apps.get_model(label)
        rows = list(model.objects.filter(scope).order_by("pk").values(*(fields or [])).distinct())
        # Raw values never leave this function: no account secret or intake body is read.
        entries.append(
            {
                "model": label,
                "purpose": purpose,
                "count": len(rows),
                "state_digest": fingerprint(canonical(rows)),
                "disposition": "review_required",
            }
        )
    for field in ["categories", "services", "travel_areas"]:
        through = apps.get_model("listings.Revision")._meta.get_field(field).remote_field.through
        rows = list(
            through.objects.filter(revision__listing__person=person).order_by("pk").values()
        )
        entries.append(
            {
                "model": "listings.Revision." + field,
                "purpose": "publication",
                "count": len(rows),
                "state_digest": fingerprint(canonical(rows)),
                "disposition": "review_required",
            }
        )
    blobs = Blob.objects.filter(photos__revision__listing__person=person).distinct().order_by("pk")
    media = []
    for blob in blobs:
        media.append(
            {
                "blob": str(blob.pk),
                "shared_reference": Photo.objects.filter(blob=blob)
                .exclude(revision__listing__person=person)
                .exists(),
                "state_digest": fingerprint(
                    canonical(
                        {
                            "status": blob.status,
                            "original": blob.original.name,
                            "derivative": blob.derivative.name,
                            "sha256": blob.sha256,
                            "phash": blob.phash,
                            "signature": blob.signature,
                            "regional_hashes": blob.regional_hashes,
                        }
                    )
                ),
            }
        )
    shared_phone = bool(
        person.phone_claim_id
        and Person.objects.filter(phone_claim_id=person.phone_claim_id)
        .exclude(pk=person.pk)
        .exists()
    )
    cross_role = bool(
        subject
        and (
            Agency.objects.filter(owner_id=subject).exists()
            or AgencyMember.objects.filter(user_id=subject).exists()
            or Person.objects.filter(individual_id=subject).exclude(pk=person.pk).exists()
            or Person.objects.filter(assigned_editor_id=subject).exclude(pk=person.pk).exists()
            or person.subject.groups.exists()
            or person.subject.user_permissions.exists()
            or person.subject.is_staff
            or person.subject.is_superuser
        )
    )
    return {
        "schema": "erasure-inventory-v1",
        "person": str(person.pk),
        "manager_version": person.manager_version,
        "entries": entries,
        "media": media,
        "shared_phone": shared_phone,
        "account_has_other_responsibilities": cross_role,
        "execution_ready": False,
        "pending": [
            "per_purpose_legal_review",
            "dependent_evidence_and_third_party_redaction",
            "unlinked_account_or_orphaned_resources",
            "sessions_logs_cache_cdn_and_backups",
            "recipient_notifications",
            "execution_and_restore_tombstones",
        ],
    }


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, key, version, purpose):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
    ):
        raise PermissionDenied
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    if (
        case.kind != "erase"
        or case.version != version
        or case.assigned_to_id != user.pk
        or not 20 <= len(purpose.strip()) <= 200
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect assigned current erasure request / Consulta la solicitud de supresión asignada actual"
        )
    proof = authorized_proof(case, person, "erase")
    signature = fingerprint(canonical({"version": version, "purpose": purpose}))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "erasure_inventory"
            and previous.payload_digest == signature
        ):
            return ErasureInventory.objects.get(action=previous)
        raise ValidationError("Conflicting action key / Clave incompatible")
    manifest = source_manifest(person, case)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="erasure_inventory",
                payload_digest=signature,
                encrypted_reason=seal({"reason": purpose}),
            )
            return ErasureInventory.objects.create(
                action=action,
                proof=proof,
                person=person,
                account_subject_id=case.account_subject_id,
                source_digest=fingerprint(canonical(manifest)),
                encrypted_manifest=seal(manifest),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error


class InventoryForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    purpose = forms.CharField(
        min_length=20, max_length=200, label="Finalidad de preparación / Preparation purpose"
    )


@login_required
@sensitive_post_parameters("purpose")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inspect(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    if case.kind != "erase":
        return private(HttpResponse("Unsupported request type", status=409))
    form = InventoryForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    manifest = None
    inventory = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            inventory = prepare(request.user, case.pk, **form.cleaned_data)
            manifest = unseal(inventory.encrypted_manifest)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
    return private(
        render(
            request,
            "safety/erasure_inventory.html",
            {"case": case, "form": form, "manifest": manifest, "inventory": inventory},
            status=status,
        )
    )
