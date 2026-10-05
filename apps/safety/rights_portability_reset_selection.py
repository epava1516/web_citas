"""Explicit, audited empty draft replacing prior choices without deleting their history."""

from uuid import UUID, uuid5

from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .models import RightsAction, RightsPortabilitySelection
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import canonical, reviewer_case
from .rights_portability_selection_store import save_selection
from .rights_portability_use import consume_approved


@transaction.atomic
@sensitive_variables()
def reset_selection(
    user,
    case_id,
    version,
    review_id,
    key,
    reason,
    previous_id,
    previous_version,
    previous_digest,
    confirmed,
):
    if confirmed is not True or type(previous_version) is not int or previous_version < 1:
        raise ValidationError("Explicit confirmation and previous draft version required")
    case, _, _ = reviewer_case(user, case_id)
    fresh_authority(user, case, user.session_version, user.mfa_version)
    baseline = (
        RightsPortabilitySelection.objects.select_for_update()
        .filter(
            pk=previous_id,
            request=case,
            actor=user,
            version=previous_version,
            selection_digest=previous_digest,
        )
        .first()
    )
    if baseline is None:
        raise ValidationError("Portability reset baseline changed")
    latest = (
        RightsPortabilitySelection.objects.filter(request=case, actor=user)
        .order_by("-version")
        .first()
    )
    retry = RightsPortabilitySelection.objects.filter(
        action__key=key, request=case, actor=user
    ).first()
    if retry is None and latest.pk != baseline.pk:
        raise ValidationError("Portability reset version changed")
    try:
        evaluation_key = uuid5(UUID(str(key)), "portability-reset-evaluation-v1")
    except (ValueError, TypeError, AttributeError) as error:
        raise ValidationError("Invalid reset key") from error
    if (
        retry is not None
        and not RightsAction.objects.filter(
            key=evaluation_key, request=case, actor=user, operation="selection_reset"
        ).exists()
    ):
        raise ValidationError("Conflicting portability reset key")
    _, assessment = consume_approved(
        user,
        case_id,
        version,
        review_id,
        evaluation_key,
        reason,
        selection_binding=fingerprint(
            canonical(
                {
                    "reset": str(key),
                    "previous": baseline.pk,
                    "version": baseline.version,
                    "digest": baseline.selection_digest,
                }
            )
        ),
        audit_operation="selection_reset",
    )
    selectors = {
        name: [] for name, item in assessment.items() if item["status"] in {"eligible", "granular"}
    }
    return save_selection(
        user, case_id, version, review_id, key, previous_version, reason, selectors
    )
