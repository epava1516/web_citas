"""Audited scalar candidates for guided selection; cataloguing never selects data."""

from itertools import islice

from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .rights import fingerprint
from .rights_copy_inspection import SECTIONS
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_portability_selection import row_reference
from .rights_portability_use import consume_approved

FIELD_PAGE_SIZE = 50


def scalar_fields(value, prefix=""):
    """Walk individual leaves with RFC6901 paths; containers are never choices."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValidationError("Invalid portability object key")
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from scalar_fields(child, prefix + "/" + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from scalar_fields(child, prefix + "/" + str(index))
    elif prefix:
        yield {"path": prefix, "value": value}
    else:
        raise ValidationError("Portability row requires an object or list")


@transaction.atomic
@sensitive_variables()
def inspect_catalog(
    user, case_id, version, review_id, key, purpose, dataset, row_index=0, field_page=1
):
    if (
        not isinstance(dataset, str)
        or dataset not in SECTIONS
        or type(row_index) is not int
        or row_index < 0
        or type(field_page) is not int
        or field_page < 1
        or not isinstance(purpose, str)
        or not 20 <= len(purpose.strip()) <= 200
    ):
        raise ValidationError("Invalid portability catalog page")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    review, assessment = consume_approved(
        actor,
        case_id,
        version,
        review_id,
        key,
        purpose,
        selection_binding=fingerprint(
            canonical(
                {
                    "dataset": dataset,
                    "row": row_index,
                    "field_page": field_page,
                }
            )
        ),
        audit_operation="selection_catalog",
    )
    if assessment[dataset]["status"] not in {"eligible", "granular"}:
        raise ValidationError("Dataset requires eligible reviewed conditions")
    source = source_copy(person, listing, case)
    if fingerprint(canonical(source)) != review.source_digest:
        raise ValidationError("Portability catalog source changed")
    rows = SECTIONS[dataset](source)
    if not rows:
        if row_index or field_page != 1:
            raise ValidationError("Portability catalog page unavailable")
        reference, fields, more = None, [], False
    else:
        if row_index >= len(rows):
            raise ValidationError("Portability catalog row unavailable")
        row = rows[row_index]
        reference = row_reference(dataset, row_index, row)
        start = (field_page - 1) * FIELD_PAGE_SIZE
        fields = list(islice(scalar_fields(row), start, start + FIELD_PAGE_SIZE + 1))
        if field_page > 1 and not fields:
            raise ValidationError("Portability catalog page unavailable")
        more = len(fields) > FIELD_PAGE_SIZE
        fields = fields[:FIELD_PAGE_SIZE]
    fresh_authority(actor, case, session_version, mfa_version)
    if (
        can_prepare(User.objects.get(pk=actor.pk), case, person).pk != review.proof_id
        or fingerprint(canonical(source_copy(person, listing, case))) != review.source_digest
    ):
        raise ValidationError("Portability catalog authority or source changed")
    return {
        "dataset": dataset,
        "row": reference,
        "row_index": row_index,
        "row_count": len(rows),
        "field_page": field_page,
        "fields": fields,
        "has_next_fields": more,
        "has_next_row": row_index + 1 < len(rows),
    }
