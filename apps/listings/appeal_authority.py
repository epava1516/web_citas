"""Fresh operator gate for the two appeal review handlers."""

from apps.core.models import User


def reviewer_allowed(request):
    supplied = request.user
    if not supplied.is_authenticated:
        return False
    current = User.objects.filter(pk=supplied.pk).first()
    if current is None:
        return False
    account_version = request.session.get("account_version")
    if account_version is None and current.session_version == 0:
        # Preserve the account middleware's initial local-session compatibility.
        account_version = 0
    return bool(
        current.is_active
        and not current.account_erased_at
        and current.mfa_enabled
        and current.session_version == supplied.session_version
        and current.mfa_version == supplied.mfa_version
        and request.session.get("mfa_version") == current.mfa_version
        and account_version == current.session_version
        and current.has_perm("listings.review_listing")
    )
