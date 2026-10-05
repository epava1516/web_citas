"""Verify a published policy version; this does not constitute legal approval."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.models import LegalDocument

from .rights import fingerprint
from .rights_exports import canonical


def published_policy(document_id, language, *, expected_digest=None):
    """Call within the rights transaction, retaining the policy lock until completion."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Policy verification requires an atomic transaction")
    if language not in {"es", "en"}:
        raise ValidationError("Unsupported policy language")
    document = (
        LegalDocument.objects.select_for_update()
        .filter(pk=document_id, slug="privacy", language=language, active=True)
        .first()
    )
    if (
        document is None
        or document.published_at > timezone.now()
        or not document.title.strip()
        or not document.body.strip()
    ):
        raise ValidationError("Published privacy policy unavailable")
    snapshot = {
        "document": document.pk,
        "slug": document.slug,
        "version": document.version,
        "language": document.language,
        "title": document.title,
        "body": document.body,
        "published_at": document.published_at.isoformat(),
    }
    digest = fingerprint(canonical(snapshot))
    if expected_digest is not None and expected_digest != digest:
        raise ValidationError("Privacy policy changed")
    return document, digest
