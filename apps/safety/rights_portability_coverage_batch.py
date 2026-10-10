"""Several individually audited coverage pages in one atomic browser request."""

from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import RightsAction
from .rights import fingerprint
from .rights_exports import canonical, reviewer_case
from .rights_inspection_source import inspection_source
from .rights_portability_batch_projection import batch_projection
from .rights_portability_coverage_inspection import inspect_page
from .rights_portability_review import authorize
from .rights_verification import authorized_proof

MAX_PAGES = 4


@transaction.atomic
@sensitive_variables()
def inspect_batch(
    user,
    case_id,
    version,
    coverage_id,
    key,
    purpose,
    dataset,
    row_index=0,
    field_page=1,
    *,
    binary=False,
    page_count=MAX_PAGES,
):
    if type(page_count) is not int or not 1 <= page_count <= MAX_PAGES:
        raise ValidationError("A coverage batch contains one to four pages")
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    proof = authorized_proof(case, person, case.kind)
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "coverage": coverage_id,
                "purpose": purpose,
                "dataset": dataset,
                "row": row_index,
                "page": field_page,
                "binary": binary,
                "count": page_count,
            }
        )
    )
    action = RightsAction.objects.filter(key=key).first()
    expected = (case.pk, actor.pk, "coverage_batch", version, signature)
    if action is None:
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    operation="coverage_batch",
                    expected_version=version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": purpose}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage batch key") from error
    if (
        action.request_id,
        action.actor_id,
        action.operation,
        action.expected_version,
        action.payload_digest,
    ) != expected:
        raise ValidationError("Conflicting coverage batch key")
    try:
        if unseal(action.encrypted_reason) != {"reason": purpose}:
            raise ValidationError("Coverage batch reason changed")
    except (InvalidToken, TypeError, ValueError) as error:
        raise ValidationError("Coverage batch reason unavailable") from error
    pages = []
    summary_cache = {}
    with inspection_source(person, listing, case) as source, batch_projection(source, user, case, proof):
        for index in range(page_count):
            read, page = inspect_page(
                user,
                case_id,
                version,
                coverage_id,
                uuid5(key, f"coverage-batch-page:{index}"),
                purpose,
                dataset,
                row_index,
                field_page,
                binary=binary,
                _inspection_source=source,
                _summary_cache=summary_cache,
            )
            pages.append((read, page))
            if page["has_next_fields"]:
                field_page += 1
            elif not binary and page["has_next_row"]:
                row_index += 1
                field_page = 1
            else:
                break
    authorize(user, case)
    if authorized_proof(case, person, case.kind).pk != proof.pk:
        raise ValidationError("Coverage batch proof changed before return")
    return pages
