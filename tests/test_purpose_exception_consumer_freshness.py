"""Controlled proof-clock crossing during the real scoped PostgreSQL consumer."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from test_purpose_exception_consumption import approved, payload
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety import purpose_exceptions, rights_verification
from apps.safety.erasure_execution import execute
from apps.safety.models import (
    ErasureExecution,
    PurposeExceptionReview,
    PurposeRestriction,
    RightsAction,
)

pytestmark = pytest.mark.django_db(transaction=True)


def test_proof_expiring_during_exception_source_read_cannot_authorize_erasure(
    request, settings, monkeypatch
):
    case, actor, _, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    values = payload(case, proposal)
    original = purpose_exceptions.source_manifest
    crossed = []
    expired = proposal.proof.expires_at + timedelta(seconds=1)

    def source_then_expire(person, current):
        manifest = original(person, current)
        # Only the proof consumer's clock advances. This is not a concurrent
        # provider callback or an expiry of the independently checked proposal.
        monkeypatch.setattr(rights_verification, "timezone", SimpleNamespace(now=lambda: expired))
        crossed.append(True)
        return manifest

    monkeypatch.setattr(purpose_exceptions, "source_manifest", source_then_expire)
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **values)
    assert crossed == [True]
    case.refresh_from_db()
    review = PurposeExceptionReview.objects.get(proposal=proposal)
    assert review.consumed_action_id is None and case.version == values["version"]
    assert not ErasureExecution.objects.exists()
    assert not RightsAction.objects.filter(request=case, operation="erasure_execute").exists()
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.get().active
