from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.models import LegalDocument
from apps.safety.rights_information_policy import published_policy

pytestmark = pytest.mark.django_db(transaction=True)


def policy(**changes):
    values = dict(
        slug="privacy",
        version="synthetic-v1",
        language="es",
        title="Synthetic privacy policy",
        body="Synthetic policy content",
        published_at=timezone.now() - timedelta(days=1),
        active=True,
    )
    return LegalDocument.objects.create(**(values | changes))


def test_policy_requires_transaction_and_detects_content_change():
    row = policy()
    with pytest.raises(RuntimeError):
        published_policy(row.pk, "es")
    with transaction.atomic():
        document, digest = published_policy(row.pk, "es")
        assert document.pk == row.pk
        assert published_policy(row.pk, "es", expected_digest=digest)[1] == digest
    LegalDocument.objects.filter(pk=row.pk).update(body="Changed synthetic policy content")
    with transaction.atomic(), pytest.raises(ValidationError, match="changed"):
        published_policy(row.pk, "es", expected_digest=digest)


@pytest.mark.parametrize("change", ["inactive", "future", "empty", "language", "slug", "unknown"])
def test_policy_rejects_unpublished_or_mismatched_reference(change):
    row = policy()
    changes = {
        "inactive": {"active": False},
        "future": {"published_at": timezone.now() + timedelta(days=1)},
        "empty": {"body": "   "},
        "slug": {"slug": "terms"},
    }
    LegalDocument.objects.filter(pk=row.pk).update(**changes.get(change, {}))
    with transaction.atomic(), pytest.raises(ValidationError):
        published_policy(
            row.pk + 1000 if change == "unknown" else row.pk, "en" if change == "language" else "es"
        )
