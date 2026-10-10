"""Exact job association for rights inventories and broker projections."""

from django.db.models import Q

FIELDS = [
    "pk",
    "key",
    "request_id",
    "actor_id",
    "proof_id",
    "review_id",
    "coverage_review_id",
    "expected_version",
    "session_version",
    "mfa_version",
    "input_digest",
    "encrypted_reason",
    "expires_at",
    "state",
    "attempts",
    "attempt_token",
    "available_at",
    "lease_until",
    "dispatched_at",
    "export_id",
    "created_at",
    "finished_at",
]


def scope(*, case=None, person=None, user=None):
    if case is not None:
        person = case.person
        user = case.account_subject
    if user is not None:
        return Q(request__account_subject=user) | Q(request__person__subject=user) | Q(actor=user)
    return Q(request__person=person) if person is not None else Q(pk__in=[])


def ids(case):
    if case is None:
        return set()
    from .models import RightsPortabilityExportJob

    return set(
        str(pk)
        for pk in RightsPortabilityExportJob.objects.filter(scope(case=case)).values_list(
            "pk", flat=True
        )
    )
