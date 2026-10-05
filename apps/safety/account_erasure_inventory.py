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
        "schema": "account-erasure-inventory-v1",
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
            "third_party_redaction",
            "sessions_logs_cache_and_backups",
            "recipient_notifications",
            "execution_and_restore_tombstones",
        ],
    }
