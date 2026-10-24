"""Controlled proof expiry after source/recovery reads in real PostgreSQL erasure."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety import erasure_plans, recovery_effects, rights_verification
from apps.safety.erasure_execution import execute
from apps.safety.models import ErasureExecution, RecoveryOutbox, RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("stage", ["source", "recovery"])
def test_scoped_proof_expiring_during_read_denies_erasure_without_effects(
    request, settings, monkeypatch, stage
):
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=["account_preferences"]
    )
    proof = case.proofs.latest("created_at")
    subject = person.subject
    before = case.version, person.rights_version, subject.session_version, subject.mfa_version
    own_favorites = list(Favorite.objects.filter(user=subject).values())
    module, name = (erasure_plans, "source_manifest") if stage == "source" else (recovery_effects, "capture")
    original = getattr(module, name)
    crossed = []
    expired = proof.expires_at + timedelta(seconds=1)

    def read_then_expire(*args, **kwargs):
        value = original(*args, **kwargs)
        # A controlled consumer-clock boundary, not a provider callback or a
        # real concurrent wait. Other domain clocks retain their original time.
        monkeypatch.setattr(rights_verification, "timezone", SimpleNamespace(now=lambda: expired))
        crossed.append(stage)
        return value

    monkeypatch.setattr(module, name, read_then_expire)
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["account_preferences"]}))
    assert crossed == [stage]
    case.refresh_from_db()
    person.refresh_from_db()
    subject.refresh_from_db()
    assert (case.version, person.rights_version, subject.session_version, subject.mfa_version) == before
    assert list(Favorite.objects.filter(user=subject).values()) == own_favorites
    assert not ErasureExecution.objects.exists() and not RecoveryOutbox.objects.exists()
    assert not RightsAction.objects.filter(request=case, operation="erasure_execute").exists()
