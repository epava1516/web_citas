"""Fresh complaint authority at admission and after canonical domain locks."""

from django.core.exceptions import PermissionDenied

from apps.core.models import User


def current_actor(user, session_version, mfa_version, *, permissions=()):
    actor = User.objects.filter(pk=user.pk).first()
    if (
        actor is None
        or not actor.is_active
        or actor.account_erased_at is not None
        or not actor.mfa_enabled
        or actor.session_version != session_version
        or actor.mfa_version != mfa_version
        or not actor.has_perm("safety.review_complaint")
        or not all(actor.has_perm(permission) for permission in permissions)
    ):
        raise PermissionDenied("Current complaint authority required")
    return actor


def request_actor(request, session_version, mfa_version, *, permissions=()):
    actor = current_actor(
        request.user, session_version, mfa_version, permissions=permissions
    )
    if (
        request.session.get("account_version") != actor.session_version
        or request.session.get("mfa_version") != actor.mfa_version
    ):
        raise PermissionDenied("Current complaint session required")
    return actor
