"""Own-account inventory metadata by purpose; no implicit organization authority."""

import json

from django.apps import apps
from django.db.models import Q
from django.views.decorators.debug import sensitive_variables

from apps.core.models import Agency, AgencyMember, Person

from .rectification_account import locked_subject
from .rights import fingerprint


@sensitive_variables()
def source(case):
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
        procedure_operations.append("exception_prepare")
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
                & (~Q(request=case) if case.kind in {"restriction", "object"} else Q()),
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
    entries = []
    for label, scope, purpose, fields in specs:
        rows = list(apps.get_model(label).objects.filter(scope).order_by("pk").values(*fields))
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
