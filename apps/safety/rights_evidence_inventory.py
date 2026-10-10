"""Scoped integrity metadata; current procedure cannot invalidate itself."""

from django.db.models import Q


def specs(*, person=None, user=None, case=None):
    scope = Q(request__person=person) if person is not None else Q(pk__in=[])
    if user is not None:
        scope = (
            Q(request__account_subject=user)
            | Q(request__person__subject=user)
            | Q(request__actor=user)
        )
    if case is not None:
        scope &= ~Q(request=case)
    return [
        (
            "safety.RightsEvidenceHead",
            scope,
            "dependent_evidence",
            ["request_id", "sequence", "digest"],
        ),
        (
            "safety.RightsEvidenceEvent",
            scope,
            "dependent_evidence",
            [
                "pk",
                "request_id",
                "sequence",
                "kind",
                "source_table",
                "source_pk",
                "payload_digest",
                "previous_digest",
                "digest",
                "created_at",
            ],
        ),
    ]
