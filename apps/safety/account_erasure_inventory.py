"""Own-account inventory metadata by purpose; no implicit organization authority."""

import json

from django.apps import apps
from django.db.models import Q
from django.views.decorators.debug import sensitive_variables

from apps.core.models import Agency, AgencyMember, Person

from .rectification_account import locked_subject
from .rights import fingerprint
from .rights_notice_inventory import NOTICE_FIELDS


@sensitive_variables()
def source(case, *, capture=None):
    user = locked_subject(None, case)
    scoped_cases = Q(account_subject=user) | Q(actor=user)
    case_ids = apps.get_model("safety.RightsRequest").objects.filter(scoped_cases).values("pk")
    specs = [
        (
            "core.User",
            Q(pk=user.pk),
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
            Q(user=user),
            "authentication",
            ["pk", "purpose", "expires_at", "used_at"],
        ),
        ("core.RecoveryCode", Q(user=user), "authentication", ["pk", "used_at"]),
        (
            "listings.Favorite",
            Q(user=user),
            "account_preferences",
            ["pk", "listing_id", "created_at"],
        ),
        (
            "core.LegalAcceptance",
            Q(user=user),
            "evidence",
            ["pk", "document_id", "agency_id", "action", "created_at"],
        ),
        (
            "core.Agency",
            Q(owner=user),
            "organization_responsibilities",
            ["pk", "owner_id", "review_version"],
        ),
        (
            "core.AgencyMember",
            Q(user=user),
            "organization_responsibilities",
            ["pk", "agency_id", "user_id", "active"],
        ),
        (
            "safety.RightsRequest",
            scoped_cases,
            "third_party_evidence",
            [
                "pk",
                "kind",
                "status",
                "version",
                "response_version",
                "received_at",
                "account_subject_id",
            ],
        ),
        (
            "safety.RightsProof",
            Q(account_subject=user),
            "dependent_evidence",
            ["pk", "request_id", "case_version", "scope", "status", "expires_at"],
        ),
        (
            "safety.RightsRectificationProposal",
            Q(account_subject=user),
            "dependent_evidence",
            ["pk", "action_id", "proof_id", "source_digest", "created_at"],
        ),
        (
            "safety.RightsAccountEmailConfirmation",
            Q(subject=user),
            "dependent_evidence",
            [
                "pk",
                "proposal_id",
                "subject_id",
                "expires_at",
                "confirmed_at",
                "consumed_at",
                "revoked_at",
            ],
        ),
        (
            "safety.RightsExport",
            Q(account_subject=user),
            "transient_copy",
            ["pk", "action_id", "case_version", "account_subject_id", "expires_at", "purged_at"],
        ),
        (
            "safety.Report",
            Q(actor=user),
            "third_party_evidence",
            ["pk", "actor_id", "status", "version", "created_at"],
        ),
        (
            "listings.Appeal",
            Q(actor=user),
            "third_party_evidence",
            ["pk", "actor_id", "status", "created_at"],
        ),
    ]
    # Current inventory/plan/execution artifacts are deliberately excluded: creating
    # them must not invalidate their own source. Other cases retain their metadata.
    procedure_operations = ["erasure_inventory", "erasure_plan", "erasure_execute"]
    if case.kind == "erase":
        procedure_operations.extend(["exception_prepare", "exception_inspect", "exception_review"])
    if case.kind in {"restriction", "object"}:
        procedure_operations.extend(
            ["processing_prepare", "processing_preview", "processing_inspect", "processing_review"]
        )
    specs.extend(
        [
            (
                "core.AgencyInvitation",
                Q(agency__owner=user),
                "organization_responsibilities",
                ["pk", "agency_id", "expires_at", "accepted_at", "revoked_at"],
            ),
            (
                "safety.RightsAccess",
                (Q(request_id__in=case_ids) | Q(actor=user))
                & (~Q(request=case) if case.kind in {"restriction", "object", "erase"} else Q()),
                "dependent_evidence",
                [
                    "pk",
                    "request_id",
                    "actor_id",
                    "case_version",
                    "response_version",
                    "message_before",
                    "response_before",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAction",
                (Q(request_id__in=case_ids) | Q(actor=user))
                & ~Q(request=case, operation__in=procedure_operations),
                "dependent_evidence",
                ["pk", "request_id", "actor_id", "expected_version", "operation", "created_at"],
            ),
            (
                "safety.RightsMessage",
                Q(request_id__in=case_ids) | Q(actor=user),
                "third_party_evidence",
                ["pk", "request_id", "actor_id", "expected_version", "created_at"],
            ),
            (
                "safety.RightsProofEvent",
                Q(proof__account_subject=user) | Q(verifier=user),
                "dependent_evidence",
                ["pk", "proof_id", "verifier_id", "outcome", "expected_version", "created_at"],
            ),
            (
                "safety.RightsResponse",
                Q(request_id__in=case_ids) | Q(actor=user),
                "third_party_evidence",
                [
                    "pk",
                    "request_id",
                    "actor_id",
                    "case_version",
                    "response_version",
                    "kind",
                    "created_at",
                ],
            ),
            (
                "safety.RightsResponseAcknowledgement",
                Q(response__request_id__in=case_ids),
                "dependent_evidence",
                ["pk", "response_id", "created_at"],
            ),
            (
                "safety.RightsNotice",
                Q(response__request_id__in=case_ids),
                "dependent_evidence",
                [
                    "pk",
                    "response_id",
                    "status",
                    "recovery_version",
                    "attempts",
                    "next_attempt_at",
                    "simulated_at",
                    "created_at",
                ],
            ),
            (
                "safety.SimulatedRightsNoticeDelivery",
                Q(notice__response__request_id__in=case_ids),
                "dependent_evidence",
                ["pk", "notice_id", "procedure", "created_at"],
            ),
            (
                "safety.RightsExtension",
                Q(request_id__in=case_ids),
                "dependent_evidence",
                ["pk", "request_id", "action_id", "additional_months", "new_due_at"],
            ),
            (
                "safety.RightsExportPreview",
                Q(request_id__in=case_ids) | Q(actor=user),
                "dependent_evidence",
                ["pk", "request_id", "actor_id", "case_version", "source_digest", "created_at"],
            ),
            (
                "safety.RightsExportDownload",
                Q(export__account_subject=user) | Q(actor=user),
                "dependent_evidence",
                ["pk", "export_id", "actor_id", "part_id", "created_at"],
            ),
            (
                "safety.Complaint",
                Q(actor=user),
                "third_party_evidence",
                ["pk", "actor_id", "status", "version", "created_at"],
            ),
            (
                "safety.ComplaintMessage",
                Q(actor=user) | Q(complaint__actor=user),
                "third_party_evidence",
                ["pk", "complaint_id", "actor_id", "expected_version", "created_at"],
            ),
            (
                "safety.ErasureInventory",
                Q(account_subject=user) & ~Q(action__request=case),
                "dependent_evidence",
                ["pk", "action_id", "proof_id", "source_digest", "created_at"],
            ),
            (
                "safety.ErasurePlan",
                Q(inventory__account_subject=user) & ~Q(action__request=case),
                "dependent_evidence",
                ["pk", "inventory_id", "action_id", "source_digest", "review_on", "created_at"],
            ),
            (
                "safety.ErasureExecution",
                Q(account_subject=user) & ~Q(action__request=case),
                "dependent_evidence",
                ["pk", "plan_id", "action_id", "proof_id", "created_at"],
            ),
        ]
    )

    # Procedure artifacts cannot invalidate their own preparation. Actual measures
    # remain visible, and other procedures retain their opaque integrity metadata.
    def scoped(prefix=""):
        return Q(**{prefix + "account_subject": user}) | Q(**{prefix + "person__subject": user})

    processing = scoped() & ~Q(action__request=case)
    processing_child = scoped("plan__") & ~Q(plan__action__request=case)
    restriction_child = Q(restriction__subject=user)
    exception = Q(subject=user) & ~Q(action__request=case)
    exception_child = Q(proposal__subject=user) & ~Q(proposal__action__request=case)
    retention = scoped("plan__inventory__") & ~Q(plan__action__request=case)
    retention_child = scoped("review__plan__inventory__") & ~Q(review__plan__action__request=case)
    specs.extend(
        [
            (
                "safety.ProcessingPurposePlan",
                processing,
                "dependent_evidence",
                ["pk", "action_id", "proof_id", "source_digest", "encrypted_plan", "created_at"],
            ),
            (
                "safety.ProcessingPlanRead",
                processing_child,
                "dependent_evidence",
                [
                    "pk",
                    "plan_id",
                    "action_id",
                    "proof_id",
                    "plan_digest",
                    "source_digest",
                    "created_at",
                ],
            ),
            (
                "safety.ProcessingPlanReview",
                processing_child,
                "dependent_evidence",
                [
                    "pk",
                    "plan_id",
                    "action_id",
                    "proof_id",
                    "plan_digest",
                    "source_digest",
                    "outcome",
                    "created_at",
                ],
            ),
            (
                "safety.ProcessingExecution",
                scoped() & ~Q(action__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "publication_hold_id",
                    "review_id",
                    "proof_id",
                    "source_digest",
                    "encrypted_result",
                    "created_at",
                ],
            ),
            (
                "safety.PurposeRestriction",
                Q(subject=user),
                "dependent_evidence",
                [
                    "pk",
                    "execution_id",
                    "purpose",
                    "mode",
                    "version",
                    "active",
                    "initial_review_on",
                    "review_on",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPortabilityRead",
                (
                    Q(assessment__request__account_subject=user)
                    | Q(assessment__request__person__subject=user)
                )
                & ~Q(assessment__request=case),
                "dependent_evidence",
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
                (
                    Q(assessment__request__account_subject=user)
                    | Q(assessment__request__person__subject=user)
                )
                & ~Q(assessment__request=case),
                "dependent_evidence",
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
                (
                    Q(selection__request__account_subject=user)
                    | Q(selection__request__person__subject=user)
                )
                & ~Q(selection__request=case),
                "dependent_evidence",
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
                (
                    Q(selection__request__account_subject=user)
                    | Q(selection__request__person__subject=user)
                )
                & ~Q(selection__request=case),
                "dependent_evidence",
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
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
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
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
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
                (
                    Q(coverage__request__account_subject=user)
                    | Q(coverage__request__person__subject=user)
                )
                & ~Q(coverage__request=case),
                "dependent_evidence",
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
                (
                    Q(coverage__request__account_subject=user)
                    | Q(coverage__request__person__subject=user)
                )
                & ~Q(coverage__request=case),
                "dependent_evidence",
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
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
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
                (
                    Q(selection__request__account_subject=user)
                    | Q(selection__request__person__subject=user)
                )
                & ~Q(selection__request=case),
                "dependent_evidence",
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
                "safety.RecoveryApplication",
                Q(scope="account", subject_reference=str(user.pk))
                | Q(
                    scope="person",
                    subject_reference__in=[
                        str(pk)
                        for pk in Person.objects.filter(subject=user).values_list("pk", flat=True)
                    ],
                ),
                "dependent_evidence",
                [
                    "pk",
                    "scope",
                    "subject_reference",
                    "receipt_digest",
                    "encrypted_receipt",
                    "created_at",
                ],
            ),
            (
                "safety.RecoveryMediaJob",
                Q(application__scope="account", application__subject_reference=str(user.pk))
                | Q(
                    application__scope="person",
                    application__subject_reference__in=[
                        str(pk)
                        for pk in Person.objects.filter(subject=user).values_list("pk", flat=True)
                    ],
                ),
                "dependent_evidence",
                [
                    "pk",
                    "application_id",
                    "blob_id",
                    "blob_reference",
                    "encrypted_paths",
                    "status",
                    "attempts",
                    "next_attempt_at",
                    "completed_at",
                    "created_at",
                ],
            ),
            (
                "safety.RecoveryOutbox",
                (Q(execution__account_subject=user) | Q(execution__person__subject=user))
                & ~Q(execution__action__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "event_id",
                    "execution_id",
                    "encrypted_event",
                    "sequence",
                    "encoded_record",
                    "created_at",
                    "exported_at",
                ],
            ),
            (
                "safety.RightsAccessClosure",
                (
                    Q(review__draft__request__account_subject=user)
                    | Q(review__draft__request__person__subject=user)
                )
                & ~Q(review__draft__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "response_id",
                    "review_id",
                    "closed_case_version",
                    "closed_response_version",
                    "channel_digest",
                    "original_session_version",
                    "original_mfa_version",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPortabilityClosure",
                (
                    Q(review__draft__request__account_subject=user)
                    | Q(review__draft__request__person__subject=user)
                )
                & ~Q(review__draft__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "response_id",
                    "review_id",
                    "closed_case_version",
                    "closed_response_version",
                    "channel_digest",
                    "original_session_version",
                    "original_mfa_version",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccessCoverageReview",
                (
                    Q(coverage__request__account_subject=user)
                    | Q(coverage__request__person__subject=user)
                )
                & ~Q(coverage__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "coverage_id",
                    "read_action_id",
                    "accounting_digest",
                    "ciphertext_digest",
                    "original_session_version",
                    "original_mfa_version",
                    "outcome",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccessResponseReview",
                (Q(draft__request__account_subject=user) | Q(draft__request__person__subject=user))
                & ~Q(draft__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "draft_id",
                    "read_action_id",
                    "text_digest",
                    "ciphertext_digest",
                    "original_session_version",
                    "original_mfa_version",
                    "outcome",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPortabilityResponseReview",
                (Q(draft__request__account_subject=user) | Q(draft__request__person__subject=user))
                & ~Q(draft__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "draft_id",
                    "read_action_id",
                    "text_digest",
                    "ciphertext_digest",
                    "original_session_version",
                    "original_mfa_version",
                    "outcome",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccessFieldDecision",
                (
                    Q(inventory__request__account_subject=user)
                    | Q(inventory__request__person__subject=user)
                )
                & ~Q(inventory__request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "inventory_id",
                    "read_action_id",
                    "encrypted_body",
                    "expires_at",
                    "purged_at",
                    "review_action_id",
                    "outcome",
                    "review_read_action_id",
                    "reviewer_session_version",
                    "reviewer_mfa_version",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccessScopeInventory",
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "request_id",
                    "actor_id",
                    "proof_id",
                    "case_version",
                    "response_version",
                    "original_session_version",
                    "original_mfa_version",
                    "source_digest",
                    "encrypted_inventory",
                    "expires_at",
                    "purged_at",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccessCoverage",
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "request_id",
                    "actor_id",
                    "export_id",
                    "information_review_id",
                    "proof_id",
                    "case_version",
                    "response_version",
                    "original_session_version",
                    "original_mfa_version",
                    "export_digest",
                    "binding_digest",
                    "accounting_digest",
                    "encrypted_coverage",
                    "expires_at",
                    "purged_at",
                    "created_at",
                ],
            ),
            (
                "safety.RightsAccessResponseDraft",
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "request_id",
                    "actor_id",
                    "export_id",
                    "information_review_id",
                    "coverage_review_id",
                    "proof_id",
                    "case_version",
                    "response_version",
                    "original_session_version",
                    "original_mfa_version",
                    "export_digest",
                    "binding_digest",
                    "text_digest",
                    "encrypted_response",
                    "expires_at",
                    "purged_at",
                    "created_at",
                ],
            ),
            (
                "safety.RightsPortabilityResponseDraft",
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
                [
                    "pk",
                    "action_id",
                    "request_id",
                    "actor_id",
                    "export_id",
                    "coverage_review_id",
                    "proof_id",
                    "case_version",
                    "response_version",
                    "original_session_version",
                    "original_mfa_version",
                    "export_digest",
                    "coverage_digest",
                    "text_digest",
                    "encrypted_response",
                    "expires_at",
                    "purged_at",
                    "created_at",
                ],
            ),
            (
                "safety.RightsExportPortabilityBinding",
                (Q(export__account_subject=user) | Q(export__person__subject=user))
                & ~Q(export__action__request=case),
                "dependent_evidence",
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
                (Q(export__account_subject=user) | Q(export__person__subject=user))
                & ~Q(export__action__request=case),
                "dependent_evidence",
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
                (
                    Q(information__request__account_subject=user)
                    | Q(information__request__person__subject=user)
                )
                & ~Q(information__request=case),
                "dependent_evidence",
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
                (
                    Q(information__request__account_subject=user)
                    | Q(information__request__person__subject=user)
                )
                & ~Q(information__request=case),
                "dependent_evidence",
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
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
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
                (Q(request__account_subject=user) | Q(request__person__subject=user))
                & ~Q(request=case),
                "dependent_evidence",
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
                Q(hold__person__subject=user),
                "dependent_evidence",
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
                "safety.PurposeRestrictionRead",
                restriction_child,
                "dependent_evidence",
                ["pk", "restriction_id", "action_id", "proof_id", "source_digest", "created_at"],
            ),
            (
                "safety.PurposeReleaseProposal",
                restriction_child,
                "dependent_evidence",
                [
                    "pk",
                    "restriction_id",
                    "action_id",
                    "proof_id",
                    "source_digest",
                    "response_id",
                    "ground",
                    "resume_message_id",
                    "released_action_id",
                    "released_proof_id",
                    "released_at",
                    "created_at",
                ],
            ),
            (
                "safety.PurposeCalendarEvent",
                restriction_child,
                "dependent_evidence",
                [
                    "pk",
                    "restriction_id",
                    "action_id",
                    "expected_version",
                    "encrypted_snapshot",
                    "created_at",
                ],
            ),
            (
                "safety.PurposeExceptionProposal",
                exception,
                "dependent_evidence",
                [
                    "pk",
                    "subject_id",
                    "plan_id",
                    "action_id",
                    "proof_id",
                    "source_digest",
                    "encrypted_scope",
                    "expires_at",
                    "created_at",
                ],
            ),
            (
                "safety.PurposeExceptionRead",
                exception_child,
                "dependent_evidence",
                ["pk", "proposal_id", "action_id", "proof_id", "source_digest", "created_at"],
            ),
            (
                "safety.PurposeExceptionReview",
                exception_child,
                "dependent_evidence",
                [
                    "pk",
                    "proposal_id",
                    "action_id",
                    "proof_id",
                    "source_digest",
                    "outcome",
                    "consumed_action_id",
                    "created_at",
                ],
            ),
            (
                "safety.RetentionReview",
                retention,
                "dependent_evidence",
                [
                    "pk",
                    "plan_id",
                    "purpose",
                    "operation",
                    "initial_review_on",
                    "next_review_on",
                    "responsible_id",
                    "version",
                    "last_reviewed_at",
                    "created_at",
                ],
            ),
            (
                "safety.RetentionReviewEvent",
                retention_child,
                "dependent_evidence",
                [
                    "pk",
                    "review_id",
                    "actor_id",
                    "expected_version",
                    "case_version",
                    "operation",
                    "plan_digest",
                    "payload_digest",
                    "encrypted_reason",
                    "encrypted_result",
                    "next_review_on",
                    "created_at",
                ],
            ),
        ]
    )
    notice_scope = Q(request_id__in=case_ids) | Q(recipient=user)
    if case.kind in {"erase", "restriction", "object"}:
        notice_scope &= ~Q(request=case)
    specs.append(
        (
            "safety.RightsRecipientNotice",
            notice_scope,
            "dependent_evidence",
            NOTICE_FIELDS,
        )
    )
    entries = []
    for label, scope, purpose, fields in specs:
        queryset = apps.get_model(label).objects.filter(scope)
        rows = (
            capture(label, purpose, queryset, fields)
            if capture
            else list(queryset.order_by("pk").values(*fields))
        )
        entries.append(
            {
                "model": label,
                "purpose": purpose,
                "count": len(rows),
                "state_digest": fingerprint(json.dumps(rows, sort_keys=True, default=str)),
                "disposition": "review_required",
            }
        )
    responsibilities = bool(
        Agency.objects.filter(owner=user).exists()
        or AgencyMember.objects.filter(user=user).exists()
        or Person.objects.filter(
            Q(subject=user) | Q(individual=user) | Q(assigned_editor=user)
        ).exists()
        or user.groups.exists()
        or user.user_permissions.exists()
        or user.is_staff
        or user.is_superuser
    )
    return {
        "schema": "account-erasure-inventory-v2",
        "account_subject": str(user.pk),
        "person": None,
        "manager_version": None,
        "entries": entries,
        "media": [],
        "shared_phone": False,
        "account_has_other_responsibilities": responsibilities,
        "execution_ready": False,
        "pending": [
            "per_purpose_legal_review",
            "other_account_records_and_dependencies",
            "current_procedure_audit_excluded",
            "third_party_redaction",
            "sessions_logs_cache_and_backups",
            "recipient_notifications",
            "execution_and_restore_tombstones",
        ],
    }
