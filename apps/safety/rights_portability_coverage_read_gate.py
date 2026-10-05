"""Require exact current independent coverage pages; caller decides approval separately."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import unseal
from .models import RightsPortabilityCoverageRead
from .rights_copy_inspection import SECTIONS
from .rights_portability_catalog import FIELD_PAGE_SIZE, scalar_fields
from .rights_portability_coverage_inspection import inspect_page


def required_pages(source):
    """Every dataset, including empty ones, and at least one binary metadata page."""
    pages = []
    for dataset, reader in SECTIONS.items():
        rows = reader(source)
        if not rows:
            pages.append((dataset, 0, 1, False))
        for index, row in enumerate(rows):
            count = sum(1 for _ in scalar_fields(row))
            pages.extend(
                (dataset, index, page, False)
                for page in range(1, max(1, (count + FIELD_PAGE_SIZE - 1) // FIELD_PAGE_SIZE) + 1)
            )
    count = sum(len(row["images"]) for row in source["revisions"])
    pages.extend(("revisions", 0, page, True) for page in range(1, max(1, (count + 19) // 20) + 1))
    return pages


@sensitive_variables()
def require_complete_reads(user, case, coverage, source, *, ids=None):
    """Replay validates original read IDs; requires enclosing atomic approval operation."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Coverage page gate requires an enclosing transaction")
    if ids is not None and (
        not isinstance(ids, list)
        or any(type(pk) is not int for pk in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValidationError("Invalid coverage read references")
    reads = RightsPortabilityCoverageRead.objects.select_related("action").filter(
        coverage=coverage,
        action__actor=user,
        action__expected_version=case.version,
        proof=coverage.proof,
        source_digest=coverage.source_digest,
        coverage_digest=coverage.coverage_digest,
        original_session_version=user.session_version,
        original_mfa_version=user.mfa_version,
    )
    if ids is not None:
        reads = reads.filter(pk__in=ids)
    chosen = {}
    for read in reads.order_by("-pk"):
        chosen.setdefault((read.dataset, read.row_index, read.field_page, read.binary), read)
    required = required_pages(source)
    if set(chosen) != set(required) or (ids is not None and len(chosen) != len(ids)):
        raise ValidationError("Inspect every current coverage page before approval")
    result = []
    for dataset, row_index, page, binary in required:
        read = chosen[(dataset, row_index, page, binary)]
        try:
            reason = unseal(read.action.encrypted_reason)["reason"]
        except (InvalidToken, ValueError, TypeError, KeyError) as error:
            raise ValidationError("Coverage read reason unavailable") from error
        # Reproduce the exact audited page, validating authority, proof, source,
        # original action signature and persisted page digest. No new read replaces it.
        action, _ = inspect_page(
            user,
            case.pk,
            case.version,
            coverage.pk,
            read.action.key,
            reason,
            dataset,
            row_index,
            page,
            binary=binary,
        )
        if action.pk != read.action_id:
            raise ValidationError("Coverage read changed")
        result.append(read.pk)
    return result
