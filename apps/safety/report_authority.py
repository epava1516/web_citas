"""Current authority for private report evidence and operational alerts."""

from django.core.exceptions import PermissionDenied

from apps.core.models import User


def fresh_authority(request):
    """Recheck revocation after lock waits, including legitimate replays."""
    actor = User.objects.get(pk=request.user.pk)
    if (
        not actor.is_active
        or not actor.has_perm("safety.review_report")
        or not actor.mfa_enabled
        or actor.session_version != request.user.session_version
        or actor.mfa_version != request.user.mfa_version
        or request.session.get("mfa_version") != actor.mfa_version
        or request.session.get("account_version") != actor.session_version
    ):
        raise PermissionDenied
    return actor

