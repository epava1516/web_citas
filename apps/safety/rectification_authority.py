"""Explicit operation-scoped authority across rectification resource waits."""

from django.core.exceptions import PermissionDenied
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .rights_scope import permitted


@sensitive_variables()
def capture_authority(user, *, review=False, respond=False, recipient_review=False):
    """Keep the caller's original epochs; never acquire an operator row lock."""
    actor_id, session_version, mfa_version = user.pk, user.session_version, user.mfa_version
    permissions = ["safety.review_rights_request", "safety.execute_rights_request"]
    if review:
        permissions.append("safety.review_rectification")
    if respond:
        permissions.append("safety.respond_rights_request")

    if recipient_review:
        permissions.append("safety.review_recipient_assessment")

    @sensitive_variables()
    def check(case):
        try:
            actor = User.objects.get(pk=actor_id)
        except User.DoesNotExist as error:
            raise PermissionDenied from error
        if (
            not actor.is_active
            or actor.account_erased_at
            or not actor.mfa_enabled
            or actor.session_version != session_version
            or actor.mfa_version != mfa_version
            or not all(actor.has_perm(permission) for permission in permissions)
            or not permitted(actor, case)
        ):
            raise PermissionDenied

    return check
